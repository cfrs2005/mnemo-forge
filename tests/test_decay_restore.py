import unittest
from datetime import datetime, timedelta, timezone

from memory_middleware.models import MemoryStatus
from memory_middleware.repository import InMemoryMemoryRepository
from memory_middleware.service import MemoryService


class DecayRestoreTests(unittest.TestCase):
    def test_ninety_day_decay_and_restore(self) -> None:
        repository = InMemoryMemoryRepository()
        service = MemoryService(repository)
        created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        record = service.write(
            tenant_id="tenant_demo", subject_id="subject_demo", scope="shared",
            kind="fact", content="long lived memory", source_event_id="event_decay",
            source_service="service_a", created_at=created_at, last_activated_at=created_at,
        )
        now = created_at + timedelta(days=90)
        results = service.search("tenant_demo", "subject_demo", "shared", "long lived", now)
        self.assertEqual(len(results), 1)
        self.assertLess(results[0].decay_score, 0.2)
        self.assertEqual(results[0].memory.status, MemoryStatus.ACTIVE)

        restored = service.restore("tenant_demo", record.memory_id, now, "service_b")
        self.assertEqual(restored.status, MemoryStatus.ACTIVE)
        self.assertEqual(restored.activation_count, 1)
        refreshed = service.search("tenant_demo", "subject_demo", "shared", "long lived", now)
        self.assertGreater(refreshed[0].decay_score, results[0].decay_score)


if __name__ == "__main__":
    unittest.main()
