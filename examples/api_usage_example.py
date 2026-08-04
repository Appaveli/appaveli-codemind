#!/usr/bin/env python3
"""
Example usage of the CodeMind Web API with authentication

This script demonstrates how to:
1. Use API key authentication
2. Handle rate limiting
3. Make requests to different endpoints
4. Handle errors properly
"""

import os
import sys
from pathlib import Path

import requests

# API Configuration
# In production, load this from environment variables
API_KEY = os.environ.get("CODEMIND_API_KEY", "cm_dev_key_12345678901234567890")
BASE_URL = os.environ.get("CODEMIND_API_URL", "http://localhost:8000")


class CodeMindClient:
    """Client for the CodeMind API"""

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"X-API-Key": api_key})

    def _handle_response(self, response: requests.Response):
        """Handle API response and raise appropriate errors"""
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            raise Exception(
                "Authentication failed. Check your API key. "
                "Error: " + response.json().get("detail", "Unknown error")
            )
        elif response.status_code == 429:
            data = response.json()
            raise Exception(
                f"Rate limit exceeded. Limit: {data.get('rate_limit')} requests/minute. "
                f"Try again in 60 seconds."
            )
        else:
            raise Exception(
                f"API error {response.status_code}: {response.text}"
            )

    def check_health(self) -> dict:
        """Check API health (no authentication required)"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()

    def analyze_file(self, file_path: str, summary_only: bool = False) -> dict:
        """
        Analyze a code file for security issues and summary

        Args:
            file_path: Path to the code file to analyze
            summary_only: If True, only return summary (no detailed analysis)

        Returns:
            Analysis result with security issues and summary
        """
        with open(file_path, "rb") as f:
            response = self.session.post(
                f"{self.base_url}/analyze/upload",
                files={"file": f},
                data={"summary_only": str(summary_only).lower()},
            )

        return self._handle_response(response)

    def refactor_file(
        self, file_path: str, refactor_type: str = "general_cleanup"
    ) -> dict:
        """
        Refactor a code file

        Args:
            file_path: Path to the code file to refactor
            refactor_type: Type of refactoring to perform
                (general_cleanup, performance, readability, etc.)

        Returns:
            Refactored code and metrics
        """
        with open(file_path, "rb") as f:
            response = self.session.post(
                f"{self.base_url}/refactor/upload",
                files={"file": f},
                data={"refactor_type": refactor_type},
            )

        return self._handle_response(response)

    def security_scan(self, file_or_zip_path: str) -> dict:
        """
        Run a security scan on a file or project (zip)

        Args:
            file_or_zip_path: Path to a single file or ZIP archive of project

        Returns:
            Security scan results with issues and recommendations
        """
        with open(file_or_zip_path, "rb") as f:
            response = self.session.post(
                f"{self.base_url}/security/upload",
                files={"file": f},
            )

        return self._handle_response(response)

    def get_rate_limit_info(self) -> dict:
        """
        Get current rate limit information from last response

        Returns:
            Dict with rate limit info
        """
        headers = self.session.headers
        return {
            "limit": headers.get("X-RateLimit-Limit"),
            "remaining": headers.get("X-RateLimit-Remaining"),
        }


def example_analyze():
    """Example: Analyze a Python file"""
    print("=" * 60)
    print("Example 1: Analyze a Python file")
    print("=" * 60)

    client = CodeMindClient(API_KEY, BASE_URL)

    # Create a sample file to analyze
    sample_code = '''
def process_user_input(user_input):
    # Security issue: Using eval() is dangerous
    result = eval(user_input)
    return result

# Another security issue: SQL injection vulnerability
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return execute_query(query)
'''

    # Write sample to temp file
    temp_file = Path("/tmp/example_analysis.py")
    temp_file.write_text(sample_code)

    try:
        result = client.analyze_file(str(temp_file))

        print(f"✅ Analysis complete!")
        print(f"   File: {result['file_path']}")
        print(f"   Language: {result['language']}")
        print(f"   Lines: {result['line_count']}")
        print(f"   Security issues found: {len(result['security_issues'])}")

        for i, issue in enumerate(result["security_issues"], 1):
            print(f"\n   Issue {i}:")
            print(f"   - Type: {issue['type']}")
            print(f"   - Severity: {issue['severity']}")
            print(f"   - Line: {issue['line']}")
            print(f"   - Description: {issue['description']}")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Clean up
        if temp_file.exists():
            temp_file.unlink()


def example_check_health():
    """Example: Check API health"""
    print("\n" + "=" * 60)
    print("Example 2: Check API Health")
    print("=" * 60)

    try:
        # Health endpoint doesn't require authentication
        response = requests.get(f"{BASE_URL}/health")
        data = response.json()

        print(f"✅ API Status: {data['status']}")
        print(f"   Service: {data['service']}")
        print(f"   Version: {data['version']}")

    except Exception as e:
        print(f"❌ Error: {e}")


def example_rate_limiting():
    """Example: Demonstrate rate limiting"""
    print("\n" + "=" * 60)
    print("Example 3: Rate Limiting")
    print("=" * 60)

    client = CodeMindClient(API_KEY, BASE_URL)

    # Create a simple test file
    temp_file = Path("/tmp/simple_test.py")
    temp_file.write_text("print('hello')")

    try:
        # Make several requests
        for i in range(5):
            result = client.analyze_file(str(temp_file))
            print(f"   Request {i + 1}: ✅ Success")

            # Check rate limit
            # Note: Rate limit headers would need to be captured from response
            # This is a simplified example

    except Exception as e:
        print(f"   ❌ Rate limit hit: {e}")
    finally:
        if temp_file.exists():
            temp_file.unlink()


def example_authentication_error():
    """Example: Show authentication error with invalid key"""
    print("\n" + "=" * 60)
    print("Example 4: Authentication Error")
    print("=" * 60)

    # Create client with invalid API key
    client = CodeMindClient("invalid_key_12345", BASE_URL)

    # Create a test file
    temp_file = Path("/tmp/auth_test.py")
    temp_file.write_text("print('test')")

    try:
        client.analyze_file(str(temp_file))
        print("   ⚠️  This should not succeed!")

    except Exception as e:
        print(f"   ✅ Expected error caught: {e}")

    finally:
        if temp_file.exists():
            temp_file.unlink()


def main():
    """Run all examples"""
    print("\n" + "🔐" * 30)
    print("CodeMind API Authentication Examples")
    print("🔐" * 30)
    print(f"\nUsing API key: {API_KEY[:20]}...")
    print(f"API URL: {BASE_URL}\n")

    # Run examples
    example_check_health()
    example_analyze()
    example_authentication_error()
    # example_rate_limiting()  # Uncomment to test rate limiting

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
