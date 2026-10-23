
import json
from pathlib import Path

from sqlalchemy import select

from app.db.database import Base, SessionLocal, engine
from app.db.models import DocumentVersion, HierarchyNode


def import_nodes(session, version_id, node, parent_id=None):
    record = HierarchyNode(
        id=node["id"],
        version_id=version_id,
        parent_id=parent_id,
        heading=node["heading"],
        level=node["level"],
        body=node["body"],
        content_hash=node["content_hash"],
        source_number=node.get("source_number"),
    )
    session.add(record)

    for child in node["children"]:
        import_nodes(session, version_id, child, node["id"])
    record.source_index = node.get("source_index", 0)


def import_manual(session, path, version_name):
    data = json.loads(path.read_text(encoding="utf-8"))

    existing = session.scalar(
        select(DocumentVersion).where(
            DocumentVersion.version_name == version_name
        )
    )

    if existing:
        print(f"Skipping {version_name}: already imported.")
        return

    version = DocumentVersion(
        version_name=version_name,
        source_filename=data["source_filename"],
        page_count=data["page_count"],
    )
    session.add(version)
    session.flush()

    import_nodes(session, version.id, data)
    print(f"Imported {version_name}.")


def main():
    Base.metadata.create_all(bind=engine)

    with SessionLocal.begin() as session:
        import_manual(
            session,
            Path("structured/ct200_manual_hierarchy.json"),
            "v1",
        )
        import_manual(
            session,
            Path("structured/ct200_manual_v2_hierarchy.json"),
            "v2",
        )


if __name__ == "__main__":
    main()
