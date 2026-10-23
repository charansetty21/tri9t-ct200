
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version_name: Mapped[str] = mapped_column(String(50), unique=True)
    source_filename: Mapped[str] = mapped_column(String(255))
    page_count: Mapped[int] = mapped_column(Integer)


class HierarchyNode(Base):
    __tablename__ = "hierarchy_nodes"

    source_index: Mapped[int] = mapped_column(Integer, default=0)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    version_id: Mapped[int] = mapped_column(
        ForeignKey("document_versions.id"),
        primary_key=True,
    )
    parent_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    heading: Mapped[str] = mapped_column(Text)
    level: Mapped[int] = mapped_column(Integer)
    body: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64))
    source_number: Mapped[str | None] = mapped_column(String(50), nullable=True)

from sqlalchemy import UniqueConstraint


class SavedSelection(Base):
    __tablename__ = "saved_selections"
    __table_args__ = (
        UniqueConstraint(
            "name",
            "version_id",
            name="uq_selection_name_version",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version_id: Mapped[int] = mapped_column(
        ForeignKey("document_versions.id"),
        nullable=False,
    )


class SelectionNode(Base):
    __tablename__ = "selection_nodes"
    __table_args__ = (
        UniqueConstraint(
            "selection_id",
            "node_id",
            "version_id",
            name="uq_selection_node_version",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    selection_id: Mapped[int] = mapped_column(
        ForeignKey("saved_selections.id"),
        nullable=False,
    )
    node_id: Mapped[str] = mapped_column(String(36), nullable=False)
    version_id: Mapped[int] = mapped_column(
        ForeignKey("document_versions.id"),
        nullable=False,
    )

class GeneratedTestCase(Base):
    __tablename__ = "generated_test_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    selection_id: Mapped[int] = mapped_column(
        ForeignKey("saved_selections.id"),
        nullable=False,
    )

    version_id: Mapped[int] = mapped_column(
        ForeignKey("document_versions.id"),
        nullable=False,
    )

    node_id: Mapped[str] = mapped_column(String(36), nullable=False)

    source_content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    preconditions: Mapped[str] = mapped_column(Text, nullable=False)
    test_steps: Mapped[str] = mapped_column(Text, nullable=False)
    expected_result: Mapped[str] = mapped_column(Text, nullable=False)

    generation_model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
