from fastapi import APIRouter, Depends, UploadFile, File
from typing import List
import tempfile
import os
from pydantic import BaseModel

from langchain_community.document_loaders import PyPDFLoader, UnstructuredMarkdownLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_openai.embeddings import OpenAIEmbeddings
from litellm import completion
from pathlib import Path
from threading import Lock

router = APIRouter()

class ChatRequest(BaseModel):
    user_query: str
    
class VectorStoreProvider:
    def __init__(self, embeddings) -> None:
        self.vector_store: FAISS | None = None
        self.embeddings = embeddings
        self._lock = Lock()
        
        
    def load(self):
        if (Path("faiss_index") / "index.faiss").exists():
            self.vector_store = FAISS.load_local("faiss_index", self.embeddings, allow_dangerous_deserialization=True)
            
    def add(self, chunks):
        with self._lock:
            if self.vector_store is None:
                self.vector_store = FAISS.from_documents(chunks, self.embeddings)
            else:
                self.vector_store.add_documents(chunks)
            
            self.vector_store.save_local("faiss_index")
            
    
vector_store_provider = VectorStoreProvider(OpenAIEmbeddings(model="text-embedding-3-large"))
vector_store_provider.load()

@router.post('/upload-pdf')
async def upload_documents(pdfs: List[UploadFile] = File(...)):

    all_docs: list[Document] = []
    
    # load pdf files
    for file in pdfs:
        # check if the file exists first
        path = Path("uploaded_docs") / (file.filename or "")

        if path.exists():
            # we have already uploaded this document
            print("we have already seen this document")
            continue
        else:
            # save the document to the local folder

            file_content = await file.read()
            path.write_bytes(file_content)
            
            if file.filename.endswith(".md"):
                print("got one markdown file")
                with tempfile.NamedTemporaryFile(delete=False, suffix='.md') as tmp:
                    tmp.write(file_content)
                    tmp_path = tmp.name
                
                    loader = UnstructuredMarkdownLoader(tmp_path)
                    docs = loader.load()
                    for doc in docs:
                        doc.metadata = {
                            "source": file.filename
                        }
                    
                    all_docs.extend(docs)
                    
            elif file.filename.endswith(".pdf"):
                print('got one pdf file')
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                    tmp.write(file_content)
                    tmp_path = tmp.name
                
                    loader = PyPDFLoader(tmp_path)
                    docs = loader.load()
                    
                    for doc in docs:
                        doc.metadata = {
                            "source": file.filename
                        }
                    
                    all_docs.extend(docs)
                    


            splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            
            chunks = splitter.create_documents(texts=[doc.page_content for doc in all_docs], metadatas=[doc.metadata for doc in all_docs])
            vector_store_provider.add(chunks)


@router.post("/chat-response")
async def chat_completion(request: ChatRequest):
    print("user asked question")

    if vector_store_provider.vector_store is not None:
        retriever = vector_store_provider.vector_store.as_retriever(search_type='similarity', search_kwargs={"k": 4})
        list_documents = retriever.invoke(request.user_query)
        
        context_document = ""
        for doc in list_documents:
            context_document += 'source: ' + doc.metadata['source'] + '\n'
            context_document += 'content: ' + doc.page_content
            
        response = completion(
            model="deepseek/deepseek-chat",
            messages=[
                {
                    "role": 'system',
                    'content': f"You are a helpful agent that will answer user's questions. some of the documents are attached for your reference that will help you answer the user's query {context_document}. If you can give user's answer from the documents then give the answer, if you cant, simply say I cant answer instead of guessing. If you are giving the answer from the documents then cite the document as well"
                },
                {
                    'role': 'user',
                    'content': request.user_query
                }
            ]
        )
        
        return {
            "answer": response.choices[0].message.content
        }
    
    return "No documents uploaded yet"