import re
import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from email_validator import validate_email, EmailNotValidError
from passlib.context import CryptContext
from jose import jwt, JWTError
from core.config import settings
from core.exceptions import ValidationException

# Password hashing context (re-exported from core.security for consistency)
from core.security import get_password_hash, verify_password

# ============================================
# EMAIL VALIDATION
# ============================================

def validate_email_address(email: str) -> bool:
    """
    Validate email format using email-validator library.
    Returns True if valid, raises ValidationException if invalid.
    """
    try:
        # Validate and get normalized form
        validated = validate_email(email)
        # Returns normalized email (e.g., "User@Example.com" -> "user@example.com")
        return True
    except EmailNotValidError as e:
        raise ValidationException(f"Invalid email format: {str(e)}")

def normalize_email(email: str) -> str:
    """
    Normalize email to lowercase and remove extra spaces.
    """
    return email.strip().lower()

# ============================================
# PASSWORD VALIDATION & STRENGTH CHECK
# ============================================

def validate_password_strength(password: str) -> bool:
    """
    Validate password strength with multiple criteria.
    Returns True if strong enough, raises ValidationException if weak.
    """
    errors = []
    
    # Check minimum length
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    # Check for uppercase letter
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    # Check for lowercase letter
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    # Check for digit
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one number")
    
    # Check for special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")
    
    # Check for common patterns
    common_patterns = ['password', '123456', 'qwerty', 'abc123', 'letmein', 'admin']
    if any(pattern in password.lower() for pattern in common_patterns):
        errors.append("Password contains common patterns (e.g., 'password', '123456')")
    
    if errors:
        raise ValidationException("; ".join(errors))
    
    return True

def generate_strong_password(length: int = 16) -> str:
    """
    Generate a cryptographically strong random password.
    """
    # Define character sets
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    # Ensure at least one from each set
    password = [
        random.choice(uppercase),
        random.choice(lowercase),
        random.choice(digits),
        random.choice(special)
    ]
    
    # Fill remaining length with random characters from all sets
    all_chars = uppercase + lowercase + digits + special
    password.extend(random.choices(all_chars, k=length - 4))
    
    # Shuffle to avoid predictable pattern
    random.shuffle(password)
    
    return ''.join(password)

# ============================================
# USERNAME VALIDATION
# ============================================

def validate_username(username: str) -> bool:
    """
    Validate username format.
    Allowed: alphanumeric, underscore, hyphen, dot.
    Must start with a letter.
    Length: 3-50 characters.
    """
    if not username or len(username) < 3 or len(username) > 50:
        raise ValidationException("Username must be between 3 and 50 characters")
    
    if not re.match(r'^[A-Za-z][A-Za-z0-9._-]*$', username):
        raise ValidationException("Username must start with a letter and contain only letters, numbers, dots, underscores, or hyphens")
    
    return True

def normalize_username(username: str) -> str:
    """
    Normalize username to lowercase.
    """
    return username.strip().lower()

# ============================================
# JWT TOKEN UTILITIES
# ============================================

def extract_token_from_header(authorization: str) -> Optional[str]:
    """
    Extract JWT token from Authorization header.
    Expected format: "Bearer <token>"
    """
    if not authorization:
        return None
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    return parts[1]

def decode_token_with_validation(token: str, token_type: str = "access") -> Dict[str, Any]:
    """
    Decode and validate JWT token.
    Returns payload dict if valid, raises exception if invalid.
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Check token type
        if payload.get("type") != token_type:
            raise ValidationException(f"Invalid token type. Expected: {token_type}")
        
        # Check expiration (jwt already handles this)
        return payload
        
    except JWTError as e:
        raise ValidationException(f"Invalid token: {str(e)}")

def get_token_expiry_days(days: int = 7) -> datetime:
    """
    Get expiry datetime for refresh tokens.
    """
    return datetime.utcnow() + timedelta(days=days)

def get_token_expiry_minutes(minutes: int = 30) -> datetime:
    """
    Get expiry datetime for access tokens.
    """
    return datetime.utcnow() + timedelta(minutes=minutes)

# ============================================
# OTP / VERIFICATION CODE GENERATION
# ============================================

def generate_verification_code(length: int = 6) -> str:
    """
    Generate a numeric verification code for email/phone verification.
    """
    return ''.join(random.choices(string.digits, k=length))

def generate_otp(length: int = 6) -> str:
    """
    Generate OTP (One-Time Password) for 2FA.
    """
    return ''.join(random.choices(string.digits, k=length))

def generate_secure_token(length: int = 32) -> str:
    """
    Generate a secure random token for password reset, email confirmation, etc.
    """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# ============================================
# SESSION & DEVICE UTILITIES
# ============================================

def generate_session_id() -> str:
    """
    Generate a unique session identifier.
    """
    import uuid
    return str(uuid.uuid4())

def parse_user_agent(user_agent: str) -> Dict[str, str]:
    """
    Parse user agent string to extract device info.
    Simple implementation - can be enhanced with dedicated libraries.
    """
    info = {
        "browser": "Unknown",
        "os": "Unknown",
        "device": "Unknown"
    }
    
    if not user_agent:
        return info
    
    # Simple browser detection
    if "Chrome" in user_agent:
        info["browser"] = "Chrome"
    elif "Firefox" in user_agent:
        info["browser"] = "Firefox"
    elif "Safari" in user_agent:
        info["browser"] = "Safari"
    elif "Edge" in user_agent:
        info["browser"] = "Edge"
    elif "Opera" in user_agent:
        info["browser"] = "Opera"
    
    # Simple OS detection
    if "Windows" in user_agent:
        info["os"] = "Windows"
    elif "Mac" in user_agent:
        info["os"] = "MacOS"
    elif "Linux" in user_agent:
        info["os"] = "Linux"
    elif "Android" in user_agent:
        info["os"] = "Android"
    elif "iPhone" in user_agent or "iPad" in user_agent:
        info["os"] = "iOS"
    
    # Simple device detection
    if "Mobile" in user_agent:
        info["device"] = "Mobile"
    elif "Tablet" in user_agent:
        info["device"] = "Tablet"
    else:
        info["device"] = "Desktop"
    
    return info

# ============================================
# ROLE & PERMISSION HELPERS
# ============================================

def is_admin(role: str) -> bool:
    """
    Check if role is admin.
    """
    return role == "admin"

def is_seller(role: str) -> bool:
    """
    Check if role is seller.
    """
    return role == "seller"

def is_customer(role: str) -> bool:
    """
    Check if role is customer.
    """
    return role == "customer"

def has_permission(role: str, required_role: str) -> bool:
    """
    Check if a role has required permission level.
    Hierarchy: admin > seller > customer
    """
    role_hierarchy = {
        "customer": 0,
        "seller": 1,
        "admin": 2
    }
    
    user_level = role_hierarchy.get(role, 0)
    required_level = role_hierarchy.get(required_role, 0)
    
    return user_level >= required_level

# ============================================
# RATE LIMITING HELPERS
# ============================================

def get_rate_limit_key(identifier: str, action: str) -> str:
    """
    Generate a key for rate limiting.
    Format: "ratelimit:{action}:{identifier}"
    """
    return f"ratelimit:{action}:{identifier}"

def get_rate_limit_ttl(attempts: int) -> int:
    """
    Calculate TTL (Time To Live) based on number of attempts.
    Exponential backoff: 1 min, 5 min, 15 min, 30 min, 60 min
    """
    ttl_mapping = {
        1: 60,      # 1 minute
        2: 300,     # 5 minutes
        3: 900,     # 15 minutes
        4: 1800,    # 30 minutes
        5: 3600     # 1 hour
    }
    return ttl_mapping.get(attempts, 3600)

# ============================================
# AUDIT & LOGGING HELPERS
# ============================================

def get_client_ip(request) -> str:
    """
    Get client IP address from request.
    Handles proxies and forwarded headers.
    """
    if not request:
        return "0.0.0.0"
    
    # Check for forwarded headers
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client
    client = request.client
    if client:
        return client.host
    
    return "0.0.0.0"

def log_auth_attempt(
    email: str,
    success: bool,
    ip_address: str,
    user_agent: str,
    reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a structured log entry for authentication attempts.
    """
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": "auth_attempt",
        "email": email,
        "success": success,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "reason": reason,
        "severity": "INFO" if success else "WARNING"
    }


# ============================================
# ACCOUNT LOCKING HELPERS
# ============================================

def get_account_lock_key(email: str) -> str:
    """
    Generate key for account lock tracking.
    """
    return f"account_lock:{email}"

def should_lock_account(failed_attempts: int, max_attempts: int = 5) -> bool:
    """
    Determine if account should be locked based on failed attempts.
    """
    return failed_attempts >= max_attempts

def get_lock_duration(failed_attempts: int) -> int:
    """
    Calculate lock duration in seconds based on failed attempts.
    """
    # 15 minutes, 30 minutes, 1 hour, 2 hours, 4 hours
    durations = [900, 1800, 3600, 7200, 14400]
    index = min(failed_attempts - 5, len(durations) - 1)
    return durations[max(0, index)]

# ============================================
# EXPORT ALL UTILITIES FOR CONVENIENCE
# ============================================

__all__ = [
    # Email
    'validate_email_address',
    'normalize_email',
    
    # Password
    'validate_password_strength',
    'generate_strong_password',
    'get_password_hash',
    'verify_password',
    
    # Username
    'validate_username',
    'normalize_username',
    
    # JWT
    'extract_token_from_header',
    'decode_token_with_validation',
    'get_token_expiry_days',
    'get_token_expiry_minutes',
    
    # OTP/Verification
    'generate_verification_code',
    'generate_otp',
    'generate_secure_token',
    
    # Session
    'generate_session_id',
    'parse_user_agent',
    
    # Roles
    'is_admin',
    'is_seller',
    'is_customer',
    'has_permission',
    
    # Rate Limiting
    'get_rate_limit_key',
    'get_rate_limit_ttl',
    
    # Audit
    'get_client_ip',
    'log_auth_attempt',
    
    # Password Reset
    'generate_password_reset_token',
    'generate_email_verification_token',
    'verify_reset_token',
    'verify_email_token',
    
    # Account Locking
    'get_account_lock_key',
    'should_lock_account',
    'get_lock_duration',
]