import unittest

from pathlib import Path

from fastapi.testclient import TestClient

from api import app, get_ingestion_pipeline, get_rag_store
from ingestion.fireflies_pipeline import IngestionResult


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_transcript.md"


class FakeStore:
     def __init__(self) -> None:
         self.projects = [
             {
                 "project_id": 1,
                 "name": "Apollo",
                 "meeting_count": 4,
                 "open_tasks": 2,
             }
         ]
 
     def list_projects(self):
         return self.projects
 
     def get_project(self, project_id):
         if project_id == 1:
             return {**self.projects[0], "phase": "Current"}
         return None
 
     def list_tasks(self, project_id=None, status=None, limit=50):  # pylint: disable=unused-argument
         return [
             {
                 "id": "task-1",
                 "title": "Coordinate site survey",
                 "status": "open",
                 "project_id": project_id,
             }
         ]
 
     def list_insights(self, project_id=None, limit=20):  # pylint: disable=unused-argument
         return [
             {
                 "id": "insight-1",
                 "summary": "Week-in-review",
                 "project_id": project_id,
             }
         ]
 
     def search_chunks_by_keyword(self, keyword, project_id=None, limit=5):  # pylint: disable=unused-argument
         return [
             {
                 "document_id": "doc-1",
                 "chunk_index": 0,
                 "text": "[00:00] Alice: kickoff",
                 "metadata": {"chunk_index": 0, "project_id": project_id},
             }
         ]
 
     def fetch_recent_chunks(self, project_id=None, limit=5):  # pylint: disable=unused-argument
         return self.search_chunks_by_keyword(None, project_id=project_id, limit=limit)
 
 
class FakePipeline:
     def __init__(self) -> None:
         self.calls = []
 
     def ingest_file(self, path, project_id=None, dry_run=True):  # pylint: disable=unused-argument
         self.calls.append((path, project_id, dry_run))
         return IngestionResult(
             document_id="doc-xyz",
             chunk_count=1,
             action_item_count=0,
             content_hash="hash",
             skipped=False,
             dry_run=dry_run,
         )
 
 
class ApiEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fake_store = FakeStore()
        cls.fake_pipeline = FakePipeline()
        app.dependency_overrides[get_rag_store] = lambda: cls.fake_store
        app.dependency_overrides[get_ingestion_pipeline] = lambda: cls.fake_pipeline
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.pop(get_rag_store, None)
        app.dependency_overrides.pop(get_ingestion_pipeline, None)

    def test_projects_endpoint_returns_projects(self):
        response = self.client.get("/api/projects")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("projects", payload)
        self.assertEqual(len(payload["projects"]), 1)

    def test_project_detail_endpoint(self):
        response = self.client.get("/api/projects/1")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("project", payload)
        self.assertEqual(payload["project"]["name"], "Apollo")
        self.assertEqual(len(payload["tasks"]), 1)

    def test_project_detail_not_found(self):
        response = self.client.get("/api/projects/999")
        self.assertEqual(response.status_code, 404)

    def test_chat_endpoint_returns_reply(self):
        response = self.client.post("/api/chat", json={"message": "What risks exist?", "project_id": 1})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("reply", payload)
        self.assertTrue(payload["reply"])
        self.assertTrue(payload["sources"])

    def test_ingest_endpoint_invokes_pipeline(self):
        response = self.client.post(
            "/api/ingest/fireflies",
            json={"path": str(FIXTURE_PATH), "project_id": 1, "dry_run": True},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.fake_pipeline.calls)
 
 
if __name__ == "__main__":
    unittest.main()
