import uvicorn

__all__ = ["app"]

def main():
    uvicorn.run("app.main:app",  host="127.0.0.1", port=8002, reload=True)


if __name__ == "__main__":
    main()
