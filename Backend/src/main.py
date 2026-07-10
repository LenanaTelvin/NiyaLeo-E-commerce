from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from core.config import settings
from core.database import engine, Base
from middleware.auth import AuthMiddleware
from middleware.logging import LoggingMiddleware

logger = logging.getLogger("freecommerce")

# ── Imports ───────────────────────────────────────────────────────────

# Auth
from modules.Auth.router import router as auth_router

# Users
from modules.users.router import router as users_router
from modules.users.admin_route import router as users_admin_router

# Sellers
from modules.sellers.router import (
    admin_router as sellers_admin_router,
    self_router  as sellers_self_router,
)

# Stores
from modules.stores.router import (
    themes_router,
    seller_router as store_seller_router,
    public_router as store_public_router,
)

# Products
from modules.products.router import (
    seller_router     as product_seller_router,
    public_router     as product_public_router,
    admin_router      as product_admin_router,
    categories_router,
    tags_router,
)

# Cart
from modules.cart.router import router as cart_router

# Reviews
from modules.reviews.router import (
    public_router as reviews_public_router,
    seller_router as reviews_seller_router,
    admin_router  as reviews_admin_router,
)

# Admin dashboard
from modules.admin.router import router as admin_dashboard_router

# Unbuilt modules — uncomment as each is completed
from modules.orders.router import (
    customer_router as orders_customer_router,
    seller_router    as orders_seller_router,
    admin_router     as orders_admin_router,
)
from modules.payments.router     import router as payments_router
# from modules.commissions.router  import router as commissions_router
# from modules.payouts.router      import router as payouts_router
# from modules.notifications.router import router as notifications_router
# from modules.analytics.router    import router as analytics_router


# ── Lifespan ──────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created / verified OK")
    except Exception as e:
        logger.error("Database connection failed at startup: %s", e)
        logger.warning("Server starting WITHOUT database — fix DATABASE_URL in .env")
    yield
    await engine.dispose()
    logger.info("Database engine disposed")


# ── App ───────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://Ni-ya-leo.vercel.app",
                   "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)
app.add_middleware(AuthMiddleware)

# ── Routers ───────────────────────────────────────────────────────────
# RULE: routers already include /api/v1 in their own prefix.
# RULE: fixed-path routers always before wildcard routers.

# Auth
app.include_router(auth_router)                 # /auth/...

# Admin dashboard — before any module-level admin routers
app.include_router(admin_dashboard_router)      # /api/v1/admin/dashboard/...

# Users
app.include_router(users_admin_router)          # /api/v1/admin/users/...
app.include_router(users_router)                # /api/v1/users/...

# Sellers — admin before self-service
app.include_router(sellers_admin_router)        # /api/v1/admin/sellers/...
app.include_router(sellers_self_router)         # /api/v1/sellers/... (wildcard last inside)

# Stores — themes and /me before slug wildcard
app.include_router(themes_router)               # /api/v1/store-themes/...
app.include_router(store_seller_router)         # /api/v1/stores/me/...
app.include_router(store_public_router)         # /api/v1/stores/{slug}/... ← last

# Products — admin and seller before public wildcard
app.include_router(categories_router)           # /api/v1/categories/...
app.include_router(tags_router)                 # /api/v1/tags/...
app.include_router(product_admin_router)        # /api/v1/admin/products/...
app.include_router(product_seller_router)       # /api/v1/seller/products/...
app.include_router(product_public_router)       # /api/v1/products/... ← last

# Cart
app.include_router(cart_router)                 # /api/v1/cart/...

# Reviews — admin and seller before public
app.include_router(reviews_admin_router)        # /api/v1/admin/reviews/...
app.include_router(reviews_seller_router)       # /api/v1/seller/reviews/...
app.include_router(reviews_public_router)       # /api/v1/reviews/... ← last

# Orders — seller/admin before customer wildcard, matching your existing convention
app.include_router(orders_admin_router)         # /api/v1/admin/orders/...
app.include_router(orders_seller_router)        # /api/v1/seller/orders/...
app.include_router(orders_customer_router)      # /api/v1/orders/...
# Payments
app.include_router(payments_router)
# app.include_router(commissions_router)        # /api/v1/commissions/...
# app.include_router(payouts_router)            # /api/v1/payouts/...
# app.include_router(notifications_router)      # /api/v1/notifications/...
# app.include_router(analytics_router)          # /api/v1/analytics/...


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": settings.APP_NAME}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )