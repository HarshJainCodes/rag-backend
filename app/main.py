from dotenv import load_dotenv
from fastapi import FastAPI
from app.api.routes.chat import router
from fastapi.middleware.cors import CORSMiddleware

import os

load_dotenv()

def createApp() -> FastAPI:
    app = FastAPI(title="Memories AI Orchestrator", version="0.1.0")

    app.include_router(router)
    # app.add_middleware(HTTPSRedirectMiddleware)
    
    cors_origins = os.getenv("CORS_ORIGINS", "https://localhost:5173").split(",")
    cors_origins = [origin.strip() for origin in cors_origins]
    
    app.add_middleware(CORSMiddleware,
        allow_origins=cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    return app

app = createApp()