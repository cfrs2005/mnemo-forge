import unittest
from pathlib import Path

from memory_middleware.api import app


class RepositoryContractTests(unittest.TestCase):
    def test_api_exposes_required_routes(self) -> None:
        routes = {route.path for route in app.routes}
        expected = {
            "/v1/memories",
            "/v1/memories/search",
            "/v1/memories/{memory_id}",
            "/v1/memories/{memory_id}/access",
            "/v1/memories/{memory_id}/feedback",
            "/v1/memories/{memory_id}/restore",
        }
        self.assertTrue(expected.issubset(routes))

    def test_postgres_adapter_uses_placeholders(self) -> None:
        source = Path("src/memory_middleware/postgres.py").read_text(encoding="utf-8")
        self.assertIn("%s", source)
        self.assertNotIn("f\"", source)


if __name__ == "__main__":
    unittest.main()
