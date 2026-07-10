"""
diagnose_mappers.py

Run this from Backend/ (same level as alembic.ini) before generating or
running migrations. It imports every model module and forces SQLAlchemy
to configure all mappers up front, so relationship() string-reference
errors surface immediately instead of failing lazily at first query time.

Usage:
    cd Backend
    python diagnose_mappers.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PROJECT_ROOT / "src"

for path in [PROJECT_ROOT, SRC_ROOT]:
    if path.exists() and str(path) not in sys.path:
        sys.path.insert(0, str(path))

print("Importing core.database.Base ...")
from core.database import Base  # noqa: E402

print("Importing Auth models ...")
from modules.Auth.models import User  # noqa: F401,E402

print("Importing users models ...")
from modules.users.models import (  # noqa: F401,E402
    UserProfile, UserAddress, UserPreference,
    UserDevice, UserActivityLog, PasswordResetToken,
    EmailVerificationToken
)

print("Importing sellers models ...")
from modules.sellers.models import (  # noqa: F401,E402
    StoreStatus, BusinessType, SellerProfile, SellerBankAccount,
    KYBInquiry, KYBInquiryStatus, UBOStatus, UBOInvitation
)

print("Importing stores models ...")
from modules.stores.models import (  # noqa: F401,E402
    StoreCustomization, StorePage, StoreSection, StoreMedia,
    StorePageType, StoreThemeType
)

print("Importing products models ...")
from modules.products.models import (  # noqa: F401,E402
    ProductStatus, ProductCondition, MediaType, StockAdjustmentReason,
    Category, Tag, Product, ProductVariant, ProductMedia, InventoryLog
)

print("Importing cart models ...")
from modules.cart.models import Cart, CartItem, CartStatus  # noqa: F401,E402

print("Importing reviews models ...")
from modules.reviews.models import Review, ReviewReply  # noqa: F401,E402

print("Importing orders models ...")
from modules.orders.models import (  # noqa: F401,E402
    Order, SellerOrder, SellerOrderItem, OrderStatusHistory
)

print("Importing payments models ...")
from modules.payments.models import Payment  # noqa: F401,E402

print("\nAll model modules imported successfully.")
print("Configuring mappers (this is where lazy relationship() errors surface)...")

from sqlalchemy.orm import configure_mappers  # noqa: E402

try:
    configure_mappers()
    print("SUCCESS: All mappers configured cleanly.\n")
except Exception as e:
    print("MAPPER CONFIGURATION FAILED:")
    print(f"  {type(e).__name__}: {e}")
    sys.exit(1)

print("Registered tables in Base.metadata:")
for table_name in sorted(Base.metadata.tables.keys()):
    print(f"  - {table_name}")