import unittest
from datetime import datetime, timezone

from mnemo_forge.models import FeedbackType
from mnemo_forge.repository import InMemoryMemoryRepository
from mnemo_forge.service import MemoryService


class FeedbackTests(unittest.TestCase):
    def test_feedback_is_idempotent_and_changes_score(self) -> None:
        repository = InMemoryMemoryRepository()
        service = MemoryService(repository)
        record = service.write(
            tenant_id="tenant_demo", subject_id="subject_demo", scope="shared",
            kind="fact", content="feedback target", source_event_id="event_feedback",
            source_service="service_a",
        )
        now = datetime.now(timezone.utc)
        service.feedback("tenant_demo", record.memory_id, "feedback_001", FeedbackType.ACCEPTED, "service_b", now)
        service.feedback("tenant_demo", record.memory_id, "feedback_001", FeedbackType.ACCEPTED, "service_b", now)
        self.assertEqual(len(repository.feedback_events), 1)
        self.assertEqual(record.feedback_score, 0.2)

        service.feedback("tenant_demo", record.memory_id, "feedback_002", FeedbackType.REJECTED, "service_b", now)
        self.assertAlmostEqual(record.feedback_score, -0.05)


if __name__ == "__main__":
    unittest.main()
