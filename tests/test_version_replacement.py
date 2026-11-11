import unittest
from datetime import datetime, timezone

from memory_middleware.repository import InMemoryMemoryRepository
from memory_middleware.service import MemoryService


class VersionReplacementTests(unittest.TestCase):
    def test_new_version_replaces_current_search_result(self) -> None:
        repository = InMemoryMemoryRepository()
        service = MemoryService(repository)
        old = service.write(
            tenant_id="tenant_demo", subject_id="subject_demo", scope="shared",
            kind="rule", content="old rule", source_event_id="event_version_1",
            source_service="service_a",
        )
        new = service.write(
            tenant_id="tenant_demo", subject_id="subject_demo", scope="shared",
            kind="rule", content="new rule", source_event_id="event_version_2",
            source_service="service_a", supersedes=old.memory_id,
        )
        current = service.search("tenant_demo", "subject_demo", "shared", "new rule", datetime.now(timezone.utc))
        self.assertEqual(len(current), 1)
        self.assertEqual(current[0].memory.memory_id, new.memory_id)
        self.assertEqual(new.version, 2)
        self.assertEqual(old.superseded_by, new.memory_id)
        self.assertEqual(repository.history("tenant_demo", new.memory_id)[0].memory_id, old.memory_id)
        self.assertIsNotNone(repository.get("tenant_demo", old.memory_id, include_history=True))


if __name__ == "__main__":
    unittest.main()
