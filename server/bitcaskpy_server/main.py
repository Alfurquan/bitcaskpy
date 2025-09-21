import argparse
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
import bitcaskpy

# Request/Response models
class PutRequest(BaseModel):
    value: str

class PutResponse(BaseModel):
    status: str
    message: str

class GetResponse(BaseModel):
    key: str
    value: Optional[str]
    found: bool

class DeleteResponse(BaseModel):
    status: str
    message: str

class HealthResponse(BaseModel):
    status: str
    version: str


def create_app(data_dir: str = "./data") -> FastAPI:
    """Create FastAPI application with BitcaskPy store"""
    app = FastAPI(
        title="BitcaskPy Server",
        description="HTTP API for BitcaskPy key-value store",
        version="0.1.0"
    )

    # Initialize store and attach to app state
    app.state.store = bitcaskpy.open_store(data_dir)

    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        return HealthResponse(status="healthy", version="0.1.0")

    @app.put("/kv/{key}", response_model=PutResponse)
    async def put_key(key: str, request: PutRequest, request_obj: Request):
        try:
            store = request_obj.app.state.store
            store.put(key, request.value)
            return PutResponse(status="success", message=f"Key '{key}' stored successfully")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/kv/{key}", response_model=GetResponse)
    async def get_key(key: str, request_obj: Request):
        try:
            store = request_obj.app.state.store
            value = store.get(key)
            return GetResponse(key=key, value=value, found=value is not None)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/kv/{key}", response_model=DeleteResponse)
    async def delete_key(key: str, request_obj: Request):
        try:
            store = request_obj.app.state.store
            store.delete(key)
            return DeleteResponse(status="success", message=f"Key '{key}' deleted successfully")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/kv", response_model=dict)
    async def list_keys(request_obj: Request):
        try:
            # store = request_obj.app.state.store
            return {"message": "Key listing not yet implemented"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return app


def main():
    parser = argparse.ArgumentParser(description="BitcaskPy HTTP Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--data-dir", default="./data", help="Data directory for storage")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")

    args = parser.parse_args()

    app = create_app(args.data_dir)

    print(f"Starting BitcaskPy Server...")
    print(f"Data directory: {args.data_dir}")
    print(f"Server will be available at: http://{args.host}:{args.port}")
    print(f"Health check: http://{args.host}:{args.port}/health")
    print(f"API docs: http://{args.host}:{args.port}/docs")

    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
