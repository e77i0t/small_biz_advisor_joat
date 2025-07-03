import logging
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from uuid import uuid4
from datetime import datetime

class ServiceBase:
    def __init__(self, service_name: str, version: str):
        self.service_name = service_name
        self.version = version
        self.app = FastAPI(
            title=f"{service_name} Service",
            version=version,
            docs_url="/docs",
            redoc_url="/redoc"
        )
        self.setup_logging()
        self.setup_middleware()
        self.setup_health_check()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        self.logger = logging.getLogger(self.service_name)

    def setup_middleware(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        class TracingMiddleware(BaseHTTPMiddleware):
            async def dispatch(inner_self, request: Request, call_next):
                trace_id = str(uuid4())
                request.state.trace_id = trace_id
                start_time = datetime.utcnow()
                response: Response = await call_next(request)
                process_time = (datetime.utcnow() - start_time).total_seconds()
                response.headers["X-Trace-ID"] = trace_id
                response.headers["X-Process-Time"] = str(process_time)
                return response

        self.app.add_middleware(TracingMiddleware)

    def setup_health_check(self):
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "ok",
                "service": self.service_name,
                "timestamp": datetime.utcnow().isoformat()
            } 