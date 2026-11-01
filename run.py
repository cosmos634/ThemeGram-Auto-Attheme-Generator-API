import uvicorn

from app.config import validate_startup_config

if __name__ == "__main__":
    validate_startup_config()
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
