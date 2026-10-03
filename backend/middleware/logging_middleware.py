import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

logger = logging.getLogger("upay_shield_access")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [CorrID: %(name)s] %(message)s"
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Rule 47: Every request must have a correlation ID
        correlation_id = (
            request.headers.get("X-Correlation-ID")
            or request.headers.get("X-Request-ID")
            or f"corr-{uuid.uuid4().hex[:12]}"
        )
        request.state.correlation_id = correlation_id
        start_time = time.time()

        try:
            response: Response = await call_next(request)
        except Exception as exc:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(
                f"[{correlation_id}] UNHANDLED ERROR: {request.method} {request.url.path} after {duration_ms}ms: {exc}",
                exc_info=True
            )
            # Rule 25 & 31: APIs must fail safely without leaking internal stack traces
            err_resp = JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": "Internal server error occurred. Please contact security operations.",
                    "correlation_id": correlation_id,
                    "error_code": "INTERNAL_SERVER_ERROR"
                }
            )
            err_resp.headers["X-Correlation-ID"] = correlation_id
            return err_resp

        duration_ms = round((time.time() - start_time) * 1000, 2)

        # Performance & Observability Headers (Rule 45, 47)
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Process-Time-Ms"] = str(duration_ms)

        # Enterprise Security Headers (Rule 31, 34)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Log API calls
        if request.url.path.startswith("/api/"):
            client_ip = request.client.host if request.client else "unknown"
            logger.info(
                f"[{correlation_id}] {request.method} {request.url.path} - "
                f"Status: {response.status_code} - {duration_ms}ms - IP: {client_ip}"
            )

        return response

