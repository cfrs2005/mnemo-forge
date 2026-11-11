import unittest
from datetime import datetime, timezone

from memory_middleware.repository import InMemoryMemoryRepository
from memory_middleware.service import MemoryService


class SharedReadTests(unittest.TestCase):
    def test_service_b_reads_service_a_memory(self) -> None:
        repository = InMemoryMemoryRepository()
        service_a = MemoryService(repository)
        service_b = MemoryService(repository)
        created = service_a.write(
            tenant_id="tenant_demo", subject_id="subject_demo", scope="shared",
            kind="preference", content="prefer evidence before a proposal",
            source_event_id="event_demo_001", source_service="service_a",
        )

        results = service_b.search(
            tenant_id="tenant_demo", subject_id="subject_demo", scope="shared",
            query="evidence proposal", now=datetime.now(timezone.utc),
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].memory.memory_id, created.memory_id)
        self.assertEqual(results[0].memory.source_service, "service_a")


if __name__ == "__main__":
    unittest.main()
