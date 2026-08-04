"""
API Key Authentication System for CodeMind Web API

Provides secure API key generation, storage, and validation with bcrypt hashing.
"""
import hashlib
import secrets
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import bcrypt


class APIKey:
    """Represents an API key with metadata."""

    def __init__(
        self,
        key_id: str,
        hashed_key: str,
        name: str,
        created_at: float,
        rate_limit: int = 100,
        is_active: bool = True,
    ):
        self.key_id = key_id
        self.hashed_key = hashed_key
        self.name = name
        self.created_at = created_at
        self.rate_limit = rate_limit
        self.is_active = is_active
        self.request_count = 0
        self.last_reset = time.time()


class APIKeyManager:
    """
    Manages API keys with secure storage and validation.

    For now, stores keys in memory (future: PostgreSQL).
    Keys are hashed with bcrypt before storage.
    """

    def __init__(self):
        self._keys: Dict[str, APIKey] = {}
        self._load_default_keys()

    def _load_default_keys(self):
        """Load or create default API keys for testing."""
        # In production, this would load from database
        # For now, create a default key for development
        default_key = "cm_dev_key_12345678901234567890"
        self._add_key_with_plaintext(
            plaintext_key=default_key,
            name="Development Key",
            rate_limit=1000
        )

    def generate_api_key(self, name: str, rate_limit: int = 100) -> str:
        """
        Generate a new API key for a user.

        Args:
            name: Descriptive name for the key
            rate_limit: Requests per minute allowed

        Returns:
            The plaintext API key (only shown once)
        """
        # Generate a cryptographically secure API key
        # Format: cm_<random_32_chars>
        random_part = secrets.token_urlsafe(24)
        api_key = f"cm_{random_part}"

        self._add_key_with_plaintext(api_key, name, rate_limit)

        return api_key

    def _add_key_with_plaintext(
        self,
        plaintext_key: str,
        name: str,
        rate_limit: int = 100
    ):
        """Internal method to add a key with plaintext (for setup)."""
        # Create a unique key ID from the plaintext
        key_id = hashlib.sha256(plaintext_key.encode()).hexdigest()[:16]

        # Hash the key with bcrypt
        hashed = bcrypt.hashpw(
            plaintext_key.encode('utf-8'),
            bcrypt.gensalt()
        )

        # Store the key
        self._keys[key_id] = APIKey(
            key_id=key_id,
            hashed_key=hashed.decode('utf-8'),
            name=name,
            created_at=time.time(),
            rate_limit=rate_limit,
        )

    def validate_key(self, api_key: str) -> Optional[APIKey]:
        """
        Validate an API key.

        Args:
            api_key: The plaintext API key to validate

        Returns:
            APIKey object if valid, None otherwise
        """
        if not api_key:
            return None

        # Generate key_id from plaintext to look up
        key_id = hashlib.sha256(api_key.encode()).hexdigest()[:16]

        stored_key = self._keys.get(key_id)
        if not stored_key:
            return None

        if not stored_key.is_active:
            return None

        # Verify the key with bcrypt
        if bcrypt.checkpw(
            api_key.encode('utf-8'),
            stored_key.hashed_key.encode('utf-8')
        ):
            return stored_key

        return None

    def check_rate_limit(self, api_key_obj: APIKey) -> bool:
        """
        Check if the API key is within rate limits.

        Args:
            api_key_obj: The validated APIKey object

        Returns:
            True if within limits, False if exceeded
        """
        current_time = time.time()

        # Reset counter every minute
        if current_time - api_key_obj.last_reset >= 60:
            api_key_obj.request_count = 0
            api_key_obj.last_reset = current_time

        # Check if under limit
        if api_key_obj.request_count >= api_key_obj.rate_limit:
            return False

        # Increment counter
        api_key_obj.request_count += 1
        return True

    def revoke_key(self, key_id: str) -> bool:
        """
        Revoke an API key.

        Args:
            key_id: The key ID to revoke

        Returns:
            True if revoked, False if not found
        """
        key = self._keys.get(key_id)
        if key:
            key.is_active = False
            return True
        return False

    def list_keys(self) -> list[Dict]:
        """
        List all API keys (without showing the actual keys).

        Returns:
            List of key metadata
        """
        return [
            {
                "key_id": key.key_id,
                "name": key.name,
                "created_at": datetime.fromtimestamp(key.created_at).isoformat(),
                "rate_limit": key.rate_limit,
                "is_active": key.is_active,
                "request_count": key.request_count,
            }
            for key in self._keys.values()
        ]


# Global instance
_api_key_manager: Optional[APIKeyManager] = None


def get_api_key_manager() -> APIKeyManager:
    """Get or create the global API key manager instance."""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager
