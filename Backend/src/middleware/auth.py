from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Pass-through middleware — JWT authentication is handled at the
    dependency level (get_current_user, get_current_seller, etc.) in
    each router, which is the correct FastAPI pattern.

    This middleware exists as a hook for future cross-cutting auth concerns
    such as:
    - Attaching a decoded token payload to request.state for logging
    - Blocking requests from banned IPs before they hit any route
    - Rate-limiting by user identity

    For now it is intentionally a no-op so startup is not blocked.
    """

    async def dispatch(self, request: Request, call_next):
        # Future: decode token and attach to request.state.user_id
        response = await call_next(request)
        return response