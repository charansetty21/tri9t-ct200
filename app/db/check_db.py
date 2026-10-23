
from sqlalchemy import func, select

from app.db.database import SessionLocal
from app.db.models import DocumentVersion, HierarchyNode


def main():
    with SessionLocal() as session:
        versions = session.scalars(
            select(DocumentVersion).order_by(DocumentVersion.id)
        ).all()

        for version in versions:
            node_count = session.scalar(
                select(func.count())
                .select_from(HierarchyNode)
                .where(HierarchyNode.version_id == version.id)
            )

            print(
                f"{version.version_name}: "
                f"{version.source_filename}, "
                f"{version.page_count} pages, "
                f"{node_count} nodes"
            )


if __name__ == "__main__":
    main()
