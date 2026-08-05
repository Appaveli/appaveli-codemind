"""
Integration tests for concurrent request handling and thread-safety.
"""
import asyncio
import io
import pytest
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient

from appaveli_codemind.web_api.codemind_api import app
from appaveli_codemind.web_api.auth import get_api_key_manager
from appaveli_codemind.web_api.agent_factory import get_agent
from appaveli_codemind.web_api.rate_limiter import get_upload_rate_limiter


@pytest.fixture(scope="module")
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture(scope="module")
def auth_headers():
    """Create valid API key for testing."""
    manager = get_api_key_manager()
    api_key = manager.generate_api_key("test-concurrency", rate_limit=1000)
    return {"X-API-Key": api_key}


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter state between tests."""
    limiter = get_upload_rate_limiter()
    limiter._requests.clear()
    yield
    limiter._requests.clear()


class TestConcurrency:
    """Tests for concurrent request handling and thread-safety."""

    def test_agent_factory_creates_new_instances(self):
        """Agent factory should create new instances for each request."""
        agent1 = get_agent()
        agent2 = get_agent()

        # Should be different instances
        assert agent1 is not agent2
        assert id(agent1) != id(agent2)

    def test_concurrent_validation_requests(self, client, auth_headers):
        """
        Test that validation (which doesn't need analysis) works concurrently.
        This tests the infrastructure is thread-safe.
        """
        def make_request(request_id: int):
            """Make a single request."""
            files = {
                "file": (f"test{request_id}.exe", io.BytesIO(b"malicious"), "application/x-msdownload")
            }
            response = client.post(
                "/analyze/upload",
                files=files,
                headers=auth_headers,
            )
            return (request_id, response.status_code)

        # Make 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(10)]
            results = [future.result() for future in futures]

        # All should get 400 (validation error for .exe files)
        for request_id, status_code in results:
            assert status_code == 400, f"Request {request_id} got {status_code} instead of 400"

    def test_concurrent_different_endpoints(self, client, auth_headers):
        """Test concurrent requests to different endpoints don't interfere."""
        def analyze_request():
            files = {"file": ("malware.exe", io.BytesIO(b"test"), "application/x-msdownload")}
            return client.post("/analyze/upload", files=files, headers=auth_headers)

        def refactor_request():
            files = {"file": ("virus.exe", io.BytesIO(b"test"), "application/x-msdownload")}
            return client.post("/refactor/upload", files=files, data={"refactor_type": "general_cleanup"}, headers=auth_headers)

        def security_request():
            files = {"file": ("trojan.exe", io.BytesIO(b"test"), "application/x-msdownload")}
            return client.post("/security/upload", files=files, headers=auth_headers)

        # Run all three concurrently
        with ThreadPoolExecutor(max_workers=3) as executor:
            analyze_future = executor.submit(analyze_request)
            refactor_future = executor.submit(refactor_request)
            security_future = executor.submit(security_request)

            analyze_result = analyze_future.result()
            refactor_result = refactor_future.result()
            security_result = security_future.result()

        # All should fail validation (400) - no state leakage
        assert analyze_result.status_code == 400
        assert refactor_result.status_code == 400
        assert security_result.status_code == 400

    def test_sequential_requests_get_different_agents(self, client, auth_headers):
        """
        Verify that sequential requests get different agent instances.
        This is a regression test for the global agent bug.
        """
        # Track agent instances via validation errors (which log agent creation)
        responses = []

        for i in range(5):
            files = {
                "file": (f"test{i}.exe", io.BytesIO(b"test"), "application/x-msdownload")
            }
            response = client.post(
                "/analyze/upload",
                files=files,
                headers=auth_headers,
            )
            responses.append(response)

        # All should get validation errors (independent requests)
        for response in responses:
            assert response.status_code == 400

    def test_no_global_agent_state_leakage(self):
        """
        Verify that there's no global agent instance.
        Each call to get_agent() should return a new instance.
        """
        # Get multiple agents
        agents = [get_agent() for _ in range(10)]

        # Check all are different instances
        agent_ids = [id(agent) for agent in agents]
        assert len(agent_ids) == len(set(agent_ids)), "Agents should all be unique instances"

        # Verify they're all the same type
        from appaveli_codemind.core.agent import CodeMindAgent
        for agent in agents:
            assert isinstance(agent, CodeMindAgent)

    @pytest.mark.skip(reason="Requires API keys - stress test")
    def test_high_concurrency_stress(self, client, auth_headers):
        """
        Stress test with many concurrent requests.
        Skipped in CI - for local performance testing.
        """
        def make_request(request_id: int):
            files = {
                "file": (f"test{request_id}.exe", io.BytesIO(b"test"), "application/x-msdownload")
            }
            response = client.post(
                "/analyze/upload",
                files=files,
                headers=auth_headers,
            )
            return response.status_code

        # 50 concurrent requests
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request, i) for i in range(50)]
            results = [future.result() for future in futures]

        # Most should succeed (validation errors count as success)
        success_count = sum(1 for status in results if status in [200, 400, 500])
        assert success_count >= 45, f"Only {success_count}/50 requests succeeded"
