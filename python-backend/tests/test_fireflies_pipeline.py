import unittest
from pathlib import Path

from ingestion.fireflies_pipeline import FirefliesIngestionPipeline


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_transcript.md"


class DummyStore:
    def __init__(self) -> None:
        self.saved_metadata = None
        self.saved_chunks = None
        self.saved_tasks = None
        self.saved_insights = None
        self.jobs_started = []
        self.jobs_completed = []

    # SupabaseRagStore interface --------------------------------------
    def find_document_by_hash(self, content_hash: str):  # pylint: disable=unused-argument
        return None

    def upsert_document_metadata(self, metadata):
        self.saved_metadata = metadata
        return metadata

    def upsert_chunks(self, chunks):
        self.saved_chunks = chunks

    def upsert_tasks(self, tasks):
        self.saved_tasks = tasks

    def insert_insight(self, insight):
        self.saved_insights = insight

    def start_ingestion_job(self, fireflies_id, content_hash):  # pylint: disable=unused-argument
        job_id = f"job-{len(self.jobs_started)+1}"
        self.jobs_started.append(job_id)
        return job_id

    def complete_ingestion_job(self, job_id, status, error=None):  # pylint: disable=unused-argument
        self.jobs_completed.append((job_id, status, error))


class FirefliesPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = DummyStore()
        self.pipeline = FirefliesIngestionPipeline(store=self.store)

    def test_parse_markdown_extracts_metadata(self):
        content = FIXTURE_PATH.read_text(encoding="utf-8")
        parsed = self.pipeline.parse_markdown(content)
        self.assertEqual(parsed.fireflies_id, "TEST-FIREFLIES-123")
        self.assertEqual(parsed.title, "Alleato Weekly Sync")
        self.assertEqual(len(parsed.attendees), 3)
        self.assertEqual(len(parsed.action_items), 3)
        self.assertGreater(len(parsed.transcript_segments), 0)

    def test_dry_run_does_not_touch_store(self):
        result = self.pipeline.ingest_file(FIXTURE_PATH, project_id=42, dry_run=True)
        self.assertTrue(result.dry_run)
        self.assertEqual(result.chunk_count, 1)
        self.assertIsNone(self.store.saved_metadata)
        self.assertIsNone(self.store.saved_chunks)
        self.assertFalse(self.store.jobs_started)

    def test_ingest_persists_chunks_and_tasks(self):
        result = self.pipeline.ingest_file(FIXTURE_PATH, project_id=99, dry_run=False)
        self.assertFalse(result.dry_run)
        self.assertIsNotNone(self.store.saved_metadata)
        self.assertIsNotNone(self.store.saved_chunks)
        self.assertEqual(len(self.store.saved_tasks), 3)
        self.assertEqual(self.store.jobs_completed[-1][1], "completed")
        # Ensure chunk metadata contains project id reference
        first_chunk = self.store.saved_chunks[0]
        self.assertEqual(first_chunk.metadata.get("project_id"), 99)


if __name__ == "__main__":
    unittest.main()
