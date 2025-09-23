import argparse
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from contextvars import ContextVar
import structlog    
import uuid
from .. import open_store
from ..logging.logger_factory import LoggerFactory


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


request_id_var: ContextVar[str] = ContextVar("request_id", default=None)
logger = LoggerFactory.get_logger(__name__, service="bitcask-server")

def create_app(data_dir: str = "./data") -> FastAPI:
    """
    Create FastAPI application with BitcaskPy store
    Args:
        data_dir (str): Directory for storing data files
    Returns:
        FastAPI app instance
    """
    app = FastAPI(
        title="BitcaskPy Server",
        description="HTTP API for BitcaskPy key-value store",
        version="0.1.0"
    )
    
    # Initialize store and attach to app state
    app.state.store = open_store(data_dir)

    # Middleware to handle request-id
    @app.middleware("http")
    async def add_request_id_header(request: Request, call_next):
        request_id = request.headers.get("x-request-id")
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Attach request_id to request.state for downstream use
        request.state.request_id = request_id

        # Bind request_id to logger context
        request_id_var.set(request_id)
        structlog.contextvars.bind_contextvars(request_id=request_id)


        # Optionally: log request start
        logger.info("Incoming request", path=request.url.path, method=request.method)

        try:
            response = await call_next(request)
        finally:
            # Clean up after request is done
            structlog.contextvars.clear_contextvars()
        
        # Add request_id to response headers
        response.headers["request-id"] = request_id
        return response

    @app.get("/health", response_model=HealthResponse)
    async def health_check(request: Request):
        return HealthResponse(status="healthy", version="0.1.0")

    @app.put("/kv/{key}", response_model=PutResponse)
    async def put_key(key: str, request: PutRequest, request_obj: Request):
        try:
            logger.info(
                "http_request_start",
                method="PUT",
                path=f"/kv/{key}",
                message=f"Storing key '{key}'"
            )
            
            store = request_obj.app.state.store
            store.put(key, request.value)
            
            logger.info(
                "http_request_end",
                method="PUT",
                path=f"/kv/{key}",
                status=200,
                message=f"Key '{key}' stored successfully"
            )
            return PutResponse(status="success", message=f"Key '{key}' stored successfully")
        except Exception as e:
            logger.error(
                "http_request_error",
                method="PUT",
                path=f"/kv/{key}",
                message=f"Error storing key '{key}'",
                error=str(e)
            )
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/kv/{key}", response_model=GetResponse)
    async def get_key(key: str, request_obj: Request):
        try:
            logger.info(
                "http_request_start",
                method="GET",
                path=f"/kv/{key}",
                message=f"Fetching key '{key}'"
            )
            
            store = request_obj.app.state.store
            value = store.get(key)
            
            logger.info(
                "http_request_end",
                method="GET",
                path=f"/kv/{key}",
                status=200,
                message=f"Key '{key}' fetched successfully",
                value_found=value is not None
            )
            return GetResponse(key=key, value=value, found=value is not None)
        except Exception as e:
            logger.error(
                "http_request_error",
                method="GET",
                path=f"/kv/{key}",
                message=f"Error fetching key '{key}'",
                error=str(e)
            )
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/kv/{key}", response_model=DeleteResponse)
    async def delete_key(key: str, request_obj: Request):
        try:
            logger.info(
                "http_request_start",
                method="DELETE",
                path=f"/kv/{key}",
                message=f"Deleting key '{key}'"
            )
            store = request_obj.app.state.store
            store.delete(key)
            logger.info(
                "http_request_end",
                method="DELETE",
                path=f"/kv/{key}",
                status=200,
                message=f"Key '{key}' deleted successfully"
            )
            return DeleteResponse(status="success", message=f"Key '{key}' deleted successfully")
        except Exception as e:
            logger.error(
                "http_request_error",
                method="DELETE",
                path=f"/kv/{key}",
                message=f"Error deleting key '{key}'",
                error=str(e)
            )
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/kv", response_model=dict)
    async def list_keys(request_obj: Request):
        try:
            return {"message": "Key listing not yet implemented"}
        except Exception as e:
            logger.error(
                "http_request_error",
                method="GET",
                path="/kv",
                message="Error listing keys",
                error=str(e)
            )
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

    logger.info("Server Starting", message="Starting BitcaskPy Server", host=args.host, port=args.port, data_dir=args.data_dir)
    logger.info("Server configuration", message=f"Server will be available at http://{args.host}:{args.port}", reload=args.reload)
    logger.info("Server configuration", message=f"Health check: http://{args.host}:{args.port}/health")

    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
