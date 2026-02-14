"""
Authentication module for user management.

This module provides secure authentication with:
- Password hashing using bcrypt
- JWT token generation with expiration
- Rate limiting on login attempts
- Input validation and SQL injection prevention
"""

import hashlib
import time
import sqlite3

# BUG: Using MD5 instead of bcrypt as documented
def hash_password(password: str) -> str:
    """Hash a password using bcrypt for secure storage."""
    return hashlib.md5(password.encode()).hexdigest()


# BUG: Token never expires despite docstring claiming expiration
def generate_token(user_id: str) -> str:
    """Generate a JWT token with 24-hour expiration."""
    return f"token_{user_id}_{int(time.time())}"


# BUG: No rate limiting implemented despite module docs
def login(username: str, password: str) -> dict:
    """
    Authenticate a user with rate limiting.

    Args:
        username: The user's username
        password: The user's password

    Returns:
        dict with 'success' and 'token' keys

    Raises:
        RateLimitError: If too many failed attempts
    """
    # BUG: SQL injection vulnerability - string formatting instead of parameterized query
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE username = '{username}' AND password_hash = '{hash_password(password)}'"
    cursor.execute(query)
    user = cursor.fetchone()
    conn.close()

    if user:
        return {"success": True, "token": generate_token(str(user[0]))}
    return {"success": False, "token": None}


def validate_email(email: str) -> bool:
    """Validate email format with RFC 5322 compliance."""
    # BUG: Extremely naive validation, not RFC 5322 compliant
    return "@" in email
