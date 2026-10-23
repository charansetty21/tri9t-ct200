
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base
from app.db.models import (
    DocumentVersion,
    GeneratedTestCase,
    HierarchyNode,
    SavedSelection,
)
from app.main import app
import app.main as main_module


@pytest.fixture
def client_and_database(monkeypatch):
    # An isolated in-memory database for each test.
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestSessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
    )

    Base.metadata.create_all(test_engine)

    with TestSessionLocal() as session:
        v1 = DocumentVersion(
            id=1,
            version_name="v1",
            source_filename="manual_v1.pdf",
            page_count=1,
        )
        v2 = DocumentVersion(
            id=2,
            version_name="v2",
            source_filename="manual_v2.pdf",
            page_count=1,
        )
        session.add_all([v1, v2])

        node_id = "test-node-1"
        session.add_all([
            HierarchyNode(
                id=node_id,
                version_id=1,
                parent_id=None,
                heading="Battery life",
                level=1,
                body="Battery lasts 300 cycles.",
                content_hash="hash-v1",
                source_number="1",
                source_index=1,
            ),
            HierarchyNode(
                id=node_id,
                version_id=2,
                parent_id=None,
                heading="Battery life",
                level=1,
                body="Battery lasts 250 cycles.",
                content_hash="hash-v2",
                source_number="1",
                source_index=1,
            ),
        ])

        selection = SavedSelection(
            id=1,
            name="Battery selection",
            version_id=1,
        )
        session.add(selection)
        session.flush()

        session.add(
            GeneratedTestCase(
                id=1,
                selection_id=1,
                version_id=1,
                node_id=node_id,
                source_content_hash="hash-v1",
                title="Battery cycle test",
                objective="Verify battery life",
                preconditions="Device has batteries installed",
                test_steps="Perform measurements",
                expected_result="Battery lasts about 300 cycles",
                generation_model="test-model",
            )
        )
        session.commit()

    monkeypatch.setattr(main_module, "SessionLocal", TestSessionLocal)

    with TestClient(app) as client:
        yield client

    Base.metadata.drop_all(test_engine)
    test_engine.dispose()


def test_selection_retrieval_marks_changed_source_stale(
    client_and_database,
):
    response = client_and_database.get("/selections/1/test-cases")

    assert response.status_code == 200
    data = response.json()
    assert data["test_case_count"] == 1
    assert data["test_cases"][0]["is_stale"] is True
    assert data["test_cases"][0]["staleness_reason"] == (
        "Source content has changed since generation."
    )


def test_node_retrieval_returns_saved_test_cases(client_and_database):
    response = client_and_database.get(
        "/nodes/test-node-1/test-cases"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["test_case_count"] == 1
    assert data["test_cases"][0]["title"] == "Battery cycle test"
    assert data["test_cases"][0]["is_stale"] is True


def test_unknown_selection_returns_404(client_and_database):
    response = client_and_database.get("/selections/999/test-cases")

    assert response.status_code == 404
