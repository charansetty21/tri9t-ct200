
from difflib import unified_diff
from app.services.staleness import is_content_stale
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from app.services.test_case_generator import generate_test_cases
from app.db.database import SessionLocal
from app.db.models import (
    DocumentVersion,
    GeneratedTestCase,
    HierarchyNode,
    SavedSelection,
    SelectionNode,
)

app = FastAPI(title="Tri9T CT-200 Manual API")


# Request model for creating a named, version-pinned selection.
class SelectionRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    version_name: str
    node_ids: list[str] = Field(min_length=1)


@app.get("/versions")
def list_versions():
    with SessionLocal() as session:
        versions = session.scalars(
            select(DocumentVersion).order_by(DocumentVersion.id)
        ).all()

        return [
            {
                "version": version.version_name,
                "filename": version.source_filename,
                "page_count": version.page_count,
            }
            for version in versions
        ]


@app.get("/versions/{version_name}/sections")
def list_top_level_sections(version_name: str):
    with SessionLocal() as session:
        version = session.scalar(
            select(DocumentVersion).where(
                DocumentVersion.version_name == version_name
            )
        )

        if version is None:
            raise HTTPException(
                status_code=404,
                detail="Version not found",
            )

        sections = session.scalars(
            select(HierarchyNode)
            .where(
                HierarchyNode.version_id == version.id,
                HierarchyNode.level == 1,
            )
            .order_by(HierarchyNode.source_index)
        ).all()

        return [
            {
                "id": node.id,
                "heading": node.heading,
                "level": node.level,
                "content_hash": node.content_hash,
            }
            for node in sections
        ]


@app.get("/versions/{version_name}/nodes/{node_id}")
def get_node(version_name: str, node_id: str):
    with SessionLocal() as session:
        version = session.scalar(
            select(DocumentVersion).where(
                DocumentVersion.version_name == version_name
            )
        )

        if version is None:
            raise HTTPException(
                status_code=404,
                detail="Version not found",
            )

        node = session.scalar(
            select(HierarchyNode).where(
                HierarchyNode.version_id == version.id,
                HierarchyNode.id == node_id,
            )
        )

        if node is None:
            raise HTTPException(
                status_code=404,
                detail="Node not found in this version",
            )

        children = session.scalars(
            select(HierarchyNode)
            .where(
                HierarchyNode.version_id == version.id,
                HierarchyNode.parent_id == node.id,
            )
            .order_by(HierarchyNode.source_index)
        ).all()

        return {
            "id": node.id,
            "version": version.version_name,
            "heading": node.heading,
            "level": node.level,
            "body": node.body,
            "content_hash": node.content_hash,
            "children": [
                {
                    "id": child.id,
                    "heading": child.heading,
                    "level": child.level,
                    "content_hash": child.content_hash,
                }
                for child in children
            ],
        }


@app.get("/versions/{version_name}/search")
def search_sections(version_name: str, q: str):
    query = q.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty",
        )

    with SessionLocal() as session:
        version = session.scalar(
            select(DocumentVersion).where(
                DocumentVersion.version_name == version_name
            )
        )

        if version is None:
            raise HTTPException(
                status_code=404,
                detail="Version not found",
            )

        pattern = f"%{query}%"

        nodes = session.scalars(
            select(HierarchyNode)
            .where(
                HierarchyNode.version_id == version.id,
                (
                    HierarchyNode.heading.ilike(pattern)
                    | HierarchyNode.body.ilike(pattern)
                ),
            )
            .order_by(HierarchyNode.source_index)
        ).all()

        return {
            "version": version_name,
            "query": query,
            "count": len(nodes),
            "results": [
                {
                    "id": node.id,
                    "heading": node.heading,
                    "body": node.body,
                    "content_hash": node.content_hash,
                }
                for node in nodes
            ],
        }


@app.get("/compare")
def compare_versions(
    old_version: str = "v1",
    new_version: str = "v2",
):
    with SessionLocal() as session:
        old = session.scalar(
            select(DocumentVersion).where(
                DocumentVersion.version_name == old_version
            )
        )
        new = session.scalar(
            select(DocumentVersion).where(
                DocumentVersion.version_name == new_version
            )
        )

        if old is None or new is None:
            raise HTTPException(
                status_code=404,
                detail="Old or new version not found",
            )

        old_nodes = session.scalars(
            select(HierarchyNode).where(
                HierarchyNode.version_id == old.id
            )
        ).all()

        new_nodes = session.scalars(
            select(HierarchyNode).where(
                HierarchyNode.version_id == new.id
            )
        ).all()

        old_map = {node.id: node for node in old_nodes}
        new_map = {node.id: node for node in new_nodes}

        added = [
            {"id": node.id, "heading": node.heading}
            for node_id, node in new_map.items()
            if node_id not in old_map
        ]

        removed = [
            {"id": node.id, "heading": node.heading}
            for node_id, node in old_map.items()
            if node_id not in new_map
        ]

        changed = []
        unchanged = []

        for node_id, before in old_map.items():
            after = new_map.get(node_id)

            if after is None:
                continue

            if before.content_hash == after.content_hash:
                unchanged.append({
                    "id": node_id,
                    "heading": after.heading,
                })
            else:
                changed.append({
                    "id": node_id,
                    "heading": after.heading,
                    "old_hash": before.content_hash,
                    "new_hash": after.content_hash,
                    "old_body": before.body,
                    "new_body": after.body,
                })

        return {
            "old_version": old_version,
            "new_version": new_version,
            "summary": {
                "added": len(added),
                "removed": len(removed),
                "changed": len(changed),
                "unchanged": len(unchanged),
            },
            "added": added,
            "removed": removed,
            "changed": changed,
            "unchanged": unchanged,
        }


@app.get("/nodes/{node_id}/changes")
def get_node_changes(
    node_id: str,
    old_version: str = "v1",
    new_version: str = "v2",
):
    with SessionLocal() as session:
        old = session.scalar(
            select(DocumentVersion).where(
                DocumentVersion.version_name == old_version
            )
        )
        new = session.scalar(
            select(DocumentVersion).where(
                DocumentVersion.version_name == new_version
            )
        )

        if old is None or new is None:
            raise HTTPException(
                status_code=404,
                detail="Old or new version not found",
            )

        before = session.scalar(
            select(HierarchyNode).where(
                HierarchyNode.version_id == old.id,
                HierarchyNode.id == node_id,
            )
        )
        after = session.scalar(
            select(HierarchyNode).where(
                HierarchyNode.version_id == new.id,
                HierarchyNode.id == node_id,
            )
        )

        if before is None and after is None:
            raise HTTPException(
                status_code=404,
                detail="Node not found in either version",
            )

        if before is None:
            return {
                "node_id": node_id,
                "old_version": old_version,
                "new_version": new_version,
                "status": "added",
                "changed": True,
                "heading": after.heading,
                "diff": [
                    f"+ {line}" for line in after.body.splitlines()
                ],
            }

        if after is None:
            return {
                "node_id": node_id,
                "old_version": old_version,
                "new_version": new_version,
                "status": "removed",
                "changed": True,
                "heading": before.heading,
                "diff": [
                    f"- {line}" for line in before.body.splitlines()
                ],
            }

        is_changed = before.content_hash != after.content_hash

        diff = []
        if is_changed:
            diff = list(
                unified_diff(
                    before.body.splitlines(),
                    after.body.splitlines(),
                    fromfile=old_version,
                    tofile=new_version,
                    lineterm="",
                )
            )

        return {
            "node_id": node_id,
            "old_version": old_version,
            "new_version": new_version,
            "status": "changed" if is_changed else "unchanged",
            "changed": is_changed,
            "heading": after.heading,
            "old_hash": before.content_hash,
            "new_hash": after.content_hash,
            "diff": diff,
        }


@app.post("/selections")
def create_selection(request: SelectionRequest):
    name = request.name.strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Selection name cannot be empty",
        )

    # Remove duplicate IDs while preserving their original order.
    node_ids = list(dict.fromkeys(request.node_ids))

    with SessionLocal() as session:
        version = session.scalar(
            select(DocumentVersion).where(
                DocumentVersion.version_name == request.version_name
            )
        )

        if version is None:
            raise HTTPException(
                status_code=404,
                detail="Document version not found",
            )

        existing = session.scalar(
            select(SavedSelection).where(
                SavedSelection.name == name,
                SavedSelection.version_id == version.id,
            )
        )

        if existing is not None:
            raise HTTPException(
                status_code=409,
                detail=(
                    "A selection with this name already exists "
                    "for this version"
                ),
            )

        nodes = session.scalars(
            select(HierarchyNode).where(
                HierarchyNode.version_id == version.id,
                HierarchyNode.id.in_(node_ids),
            )
        ).all()

        found_ids = {node.id for node in nodes}
        missing_ids = [
            node_id for node_id in node_ids
            if node_id not in found_ids
        ]

        if missing_ids:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": (
                        "Some node IDs do not belong to "
                        "the selected version"
                    ),
                    "invalid_node_ids": missing_ids,
                },
            )

        selection = SavedSelection(
            name=name,
            version_id=version.id,
        )
        session.add(selection)
        session.flush()

        for node_id in node_ids:
            session.add(
                SelectionNode(
                    selection_id=selection.id,
                    node_id=node_id,
                    version_id=version.id,
                )
            )

        session.commit()

        return {
            "selection_id": selection.id,
            "name": selection.name,
            "version": version.version_name,
            "node_ids": node_ids,
            "node_count": len(node_ids),
        }


@app.get("/selections/{selection_id}")
def get_selection(selection_id: int):
    with SessionLocal() as session:
        selection = session.get(SavedSelection, selection_id)

        if selection is None:
            raise HTTPException(
                status_code=404,
                detail="Selection not found",
            )

        version = session.get(
            DocumentVersion,
            selection.version_id,
        )

        saved_nodes = session.scalars(
            select(SelectionNode)
            .where(
                SelectionNode.selection_id == selection.id
            )
            .order_by(SelectionNode.id)
        ).all()

        result_nodes = []

        for saved_node in saved_nodes:
            node = session.scalar(
                select(HierarchyNode).where(
                    HierarchyNode.id == saved_node.node_id,
                    HierarchyNode.version_id == saved_node.version_id,
                )
            )

            if node is None:
                raise HTTPException(
                    status_code=500,
                    detail="Saved selection node could not be resolved",
                )

            result_nodes.append({
                "node_id": node.id,
                "version": version.version_name,
                "heading": node.heading,
                "body": node.body,
                "content_hash": node.content_hash,
            })

        return {
            "selection_id": selection.id,
            "name": selection.name,
            "version": version.version_name,
            "nodes": result_nodes,
        }

@app.post("/selections/{selection_id}/generate")
def generate_selection_test_cases(selection_id: int):
    with SessionLocal() as session:
        selection = session.get(SavedSelection, selection_id)

        if selection is None:
            raise HTTPException(
                status_code=404,
                detail="Selection not found",
            )

        selected_nodes = session.execute(
            select(SelectionNode, HierarchyNode)
            .join(
                HierarchyNode,
                (HierarchyNode.id == SelectionNode.node_id)
                & (HierarchyNode.version_id == SelectionNode.version_id),
            )
            .where(SelectionNode.selection_id == selection_id)
        ).all()

        if not selected_nodes:
            raise HTTPException(
                status_code=400,
                detail="Selection contains no nodes",
            )

        # Generate everything before saving, avoiding partial results
        # if the LLM fails for one of the selected nodes.
        pending_cases = []

        try:
            for selection_node, node in selected_nodes:
                source_text = f"{node.heading}\n\n{node.body}"
                cases = generate_test_cases(source_text)

                for case in cases:
                    pending_cases.append(
                        GeneratedTestCase(
                            selection_id=selection.id,
                            version_id=selection_node.version_id,
                            node_id=node.id,
                            source_content_hash=node.content_hash,
                            title=case["title"],
                            objective=case["objective"],
                            preconditions=case["preconditions"],
                            test_steps=case["test_steps"],
                            expected_result=case["expected_result"],
                            generation_model="qwen3:8b",
                        )
                    )

        except RuntimeError as exc:
            raise HTTPException(
                status_code=502,
                detail=str(exc),
            ) from exc

        session.add_all(pending_cases)
        session.commit()

        return {
            "selection_id": selection.id,
            "selection_name": selection.name,
            "source_version": selection.version_id,
            "generation_model": "qwen3:8b",
            "generated_count": len(pending_cases),
            "test_cases": [
                {
                    "id": case.id,
                    "node_id": case.node_id,
                    "source_content_hash": case.source_content_hash,
                    "title": case.title,
                    "objective": case.objective,
                    "preconditions": case.preconditions,
                    "test_steps": case.test_steps,
                    "expected_result": case.expected_result,
                }
                for case in pending_cases
            ],
        }


@app.get("/selections/{selection_id}/test-cases")
def get_selection_test_cases(selection_id: int):
    with SessionLocal() as session:
        selection = session.get(SavedSelection, selection_id)

        if selection is None:
            raise HTTPException(
                status_code=404,
                detail="Selection not found",
            )

        test_cases = session.scalars(
            select(GeneratedTestCase).where(
                GeneratedTestCase.selection_id == selection_id
            )
        ).all()

        latest_version = session.scalar(
            select(DocumentVersion)
            .order_by(DocumentVersion.id.desc())
            .limit(1)
        )

        results = []

        for case in test_cases:
            current_node = None

            if latest_version is not None:
                current_node = session.scalar(
                    select(HierarchyNode).where(
                        HierarchyNode.id == case.node_id,
                        HierarchyNode.version_id == latest_version.id,
                    )
                )

            is_stale = is_content_stale(
                case.source_content_hash,
                current_node.content_hash if current_node else None,
            )

            if current_node is None:
                staleness_reason = (
                    "Source node is missing from the latest version."
                )
            elif is_stale:
                staleness_reason = (
                    "Source content has changed since generation."
                )
            else:
                staleness_reason = (
                    "Source content matches the latest version."
                )

            results.append({
                "test_case_id": case.id,
                "selection_id": case.selection_id,
                "source_version_id": case.version_id,
                "node_id": case.node_id,
                "source_content_hash": case.source_content_hash,
                "title": case.title,
                "objective": case.objective,
                "preconditions": case.preconditions,
                "test_steps": case.test_steps,
                "expected_result": case.expected_result,
                "generation_model": case.generation_model,
                "is_stale": is_stale,
                "staleness_reason": staleness_reason,
            })

        return {
            "selection_id": selection.id,
            "selection_name": selection.name,
            "latest_version": (
                latest_version.version_name
                if latest_version is not None
                else None
            ),
            "test_case_count": len(results),
            "test_cases": results,
        }


@app.get("/nodes/{node_id}/test-cases")
def get_node_test_cases(node_id: str):
    with SessionLocal() as session:
        test_cases = session.scalars(
            select(GeneratedTestCase).where(
                GeneratedTestCase.node_id == node_id
            )
        ).all()

        latest_version = session.scalar(
            select(DocumentVersion)
            .order_by(DocumentVersion.id.desc())
            .limit(1)
        )

        results = []

        for case in test_cases:
            current_node = None

            if latest_version is not None:
                current_node = session.scalar(
                    select(HierarchyNode).where(
                        HierarchyNode.id == case.node_id,
                        HierarchyNode.version_id == latest_version.id,
                    )
                )

            is_stale = is_content_stale(
                case.source_content_hash,
                current_node.content_hash if current_node else None,
            )

            results.append({
                "test_case_id": case.id,
                "selection_id": case.selection_id,
                "source_version_id": case.version_id,
                "node_id": case.node_id,
                "title": case.title,
                "objective": case.objective,
                "preconditions": case.preconditions,
                "test_steps": case.test_steps,
                "expected_result": case.expected_result,
                "is_stale": is_stale,
            })

        return {
            "node_id": node_id,
            "latest_version": (
                latest_version.version_name
                if latest_version is not None
                else None
            ),
            "test_case_count": len(results),
            "test_cases": results,
        }
