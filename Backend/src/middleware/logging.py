import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("freecommerce.access")


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every request: method, path, status code, and response time.

    Output example:
        GET /api/v1/products/ 200  43ms
        POST /api/v1/cart/items 201  12ms
        GET /api/v1/stores/bad-slug/theme 404  8ms
    """

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()

        response = await call_next(request)

        elapsed_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "%s %s %s  %.0fms",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )

        return response