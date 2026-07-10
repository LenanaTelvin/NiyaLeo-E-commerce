# alembic/env.py
import asyncio
from logging.config import fileConfig


from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import your models here so Alembic can see them
import sys
from pathlib import Path

# Add the src directory to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

for path in [PROJECT_ROOT, SRC_ROOT]:
    if path.exists() and str(path) not in sys.path:
        sys.path.insert(0,str(path))
        
config = context.config

import os
db_url = os.getenv("DATABASE_URL")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url.replace("%", "%%"))  # Escape % for configparser

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)  

# Import all your models so Alembic can detect them
from core.database import Base
from modules.Auth.models import User # noqa: F401
from modules.users.models import ( # noqa: F401
    UserProfile, UserAddress, UserPreference,
    UserDevice, UserActivityLog, PasswordResetToken,
    EmailVerificationToken
)
from modules.sellers.models import ( # noqa: F401
    StoreStatus,BusinessType,SellerProfile, SellerBankAccount,
    KYBInquiry,KYBInquiryStatus,UBOStatus,UBOInvitation
)
from modules.stores.models import ( # noqa: F401 
    StoreCustomization, StorePage, StoreSection, StoreMedia, StorePageType,StoreThemeType
)
from modules.products.models import ( # noqa: F401
    ProductStatus,ProductCondition,MediaType, StockAdjustmentReason, Category,
    Tag, Product, ProductVariant,
    ProductMedia, InventoryLog
)
from modules.cart.models import Cart, CartItem, CartStatus  # noqa: F401 — confirm exact class names
from modules.reviews.models import Review, ReviewReply  # noqa: F401 — confirm exact class names
from modules.orders.models import Order, SellerOrder, SellerOrderItem, OrderStatusHistory  # noqa: F401
from modules.payments.models import Payment  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()