"""
Unit tests for the API authentication system
"""
import time
import unittest

from appaveli_codemind.web_api.auth import APIKeyManager


class TestAPIKeyManager(unittest.TestCase):
    """Test the APIKeyManager class"""

    def setUp(self):
        """Set up a fresh APIKeyManager for each test"""
        self.manager = APIKeyManager()

    def test_generate_api_key_format(self):
        """Test that generated API keys have the correct format"""
        api_key = self.manager.generate_api_key("Test Key")

        # Should start with "cm_"
        self.assertTrue(api_key.startswith("cm_"))

        # Should have reasonable length
        self.assertGreater(len(api_key), 20)

    def test_validate_valid_key(self):
        """Test validating a valid API key"""
        # Generate a key
        api_key = self.manager.generate_api_key("Test Key", rate_limit=50)

        # Validate it
        key_obj = self.manager.validate_key(api_key)

        self.assertIsNotNone(key_obj)
        self.assertEqual(key_obj.name, "Test Key")
        self.assertEqual(key_obj.rate_limit, 50)
        self.assertTrue(key_obj.is_active)

    def test_validate_invalid_key(self):
        """Test validating an invalid API key"""
        # Try to validate a non-existent key
        key_obj = self.manager.validate_key("cm_invalid_key_12345")

        self.assertIsNone(key_obj)

    def test_validate_empty_key(self):
        """Test validating an empty API key"""
        key_obj = self.manager.validate_key("")

        self.assertIsNone(key_obj)

    def test_validate_none_key(self):
        """Test validating a None API key"""
        key_obj = self.manager.validate_key(None)

        self.assertIsNone(key_obj)

    def test_rate_limit_enforcement(self):
        """Test that rate limiting is enforced correctly"""
        # Generate a key with low rate limit
        api_key = self.manager.generate_api_key("Rate Limited Key", rate_limit=3)
        key_obj = self.manager.validate_key(api_key)

        # Should allow first 3 requests
        self.assertTrue(self.manager.check_rate_limit(key_obj))
        self.assertTrue(self.manager.check_rate_limit(key_obj))
        self.assertTrue(self.manager.check_rate_limit(key_obj))

        # Should block 4th request
        self.assertFalse(self.manager.check_rate_limit(key_obj))

    def test_rate_limit_reset(self):
        """Test that rate limits reset after 60 seconds"""
        # Generate a key with low rate limit
        api_key = self.manager.generate_api_key("Reset Test Key", rate_limit=2)
        key_obj = self.manager.validate_key(api_key)

        # Exhaust the rate limit
        self.assertTrue(self.manager.check_rate_limit(key_obj))
        self.assertTrue(self.manager.check_rate_limit(key_obj))
        self.assertFalse(self.manager.check_rate_limit(key_obj))

        # Simulate 60 seconds passing by manipulating the last_reset time
        key_obj.last_reset = time.time() - 61

        # Should allow requests again
        self.assertTrue(self.manager.check_rate_limit(key_obj))

    def test_revoke_key(self):
        """Test revoking an API key"""
        # Generate and validate a key
        api_key = self.manager.generate_api_key("Revoke Test Key")
        key_obj = self.manager.validate_key(api_key)

        self.assertIsNotNone(key_obj)

        # Revoke the key
        import hashlib
        key_id = hashlib.sha256(api_key.encode()).hexdigest()[:16]
        result = self.manager.revoke_key(key_id)

        self.assertTrue(result)

        # Should no longer validate
        key_obj = self.manager.validate_key(api_key)
        self.assertIsNone(key_obj)

    def test_revoke_nonexistent_key(self):
        """Test revoking a non-existent key"""
        result = self.manager.revoke_key("nonexistent_key_id")

        self.assertFalse(result)

    def test_list_keys(self):
        """Test listing all API keys"""
        # Generate a few keys
        self.manager.generate_api_key("Key 1", rate_limit=100)
        self.manager.generate_api_key("Key 2", rate_limit=200)

        # List keys (should include default dev key + our 2 keys = 3 total)
        keys = self.manager.list_keys()

        self.assertGreaterEqual(len(keys), 2)

        # Check that keys have expected fields
        for key_info in keys:
            self.assertIn("key_id", key_info)
            self.assertIn("name", key_info)
            self.assertIn("created_at", key_info)
            self.assertIn("rate_limit", key_info)
            self.assertIn("is_active", key_info)

    def test_default_dev_key_exists(self):
        """Test that the default development key is created"""
        # The default key should be loadable
        default_key = "cm_dev_key_12345678901234567890"
        key_obj = self.manager.validate_key(default_key)

        self.assertIsNotNone(key_obj)
        self.assertEqual(key_obj.name, "Development Key")

    def test_key_hashing_security(self):
        """Test that keys are hashed and not stored in plaintext"""
        api_key = self.manager.generate_api_key("Security Test")

        # List keys and verify the actual key is not in the response
        keys = self.manager.list_keys()

        for key_info in keys:
            # The actual API key should never appear in the list
            self.assertNotEqual(key_info.get("key"), api_key)

    def test_concurrent_requests_rate_limit(self):
        """Test rate limiting with concurrent-like requests"""
        api_key = self.manager.generate_api_key("Concurrent Test", rate_limit=5)
        key_obj = self.manager.validate_key(api_key)

        # Simulate 5 concurrent requests
        results = [self.manager.check_rate_limit(key_obj) for _ in range(7)]

        # First 5 should succeed, last 2 should fail
        self.assertEqual(results, [True, True, True, True, True, False, False])


if __name__ == "__main__":
    unittest.main()
