import unittest
from datetime import datetime, timezone

from memory_middleware.repository import InMemoryMemoryRepository
from memory_middleware.service import MemoryService


class TenantIsolationTests(unittest.TestCase):
    def test_search_does_not_cross_tenants(self) -> None:
        repository = InMemoryMemoryRepository()
        service = MemoryService(repository)
        service.write(
            tenant_id="tenant_a", subject_id="subject_demo", scope="shared",
            kind="fact", content="tenant a private fact",
            source_event_id="event_a", source_service="service_a",
        )
        service.write(
            tenant_id="tenant_b", subject_id="subject_demo", scope="shared",
            kind="fact", content="tenant b private fact",
            source_event_id="event_b", source_service="service_b",
        )

        results = service.search(
            tenant_id="tenant_a", subject_id="subject_demo", scope="shared",
            query="private fact", now=datetime.now(timezone.utc),
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].memory.tenant_id, "tenant_a")
        self.assertIsNone(repository.get("tenant_b", results[0].memory.memory_id))


if __name__ == "__main__":
    unittest.main()
