# Technical Approach — Tri9T CT-200 Manual API

## 1. Objective

The objective is to build a version-aware document processing API that transforms PDF manuals into structured, retrievable content and generates QA test-case ideas tied to the exact document content used for generation.

The design emphasizes traceability, preservation of historical versions, explicit handling of document irregularities, and transparent staleness detection.

## 2. Architecture

The implementation is divided into five main stages.

1. **PDF extraction:** PyMuPDF extracts text blocks and available layout metadata, including page number, bounding box, and font-size information.
2. **Hierarchy construction:** Extracted blocks are converted into a source-ordered hierarchy of document nodes. Nodes retain headings, body text, hierarchy levels, parent relationships, source positions, and content hashes.
3. **Persistence and version comparison:** SQLAlchemy stores document versions and hierarchy nodes in SQLite. Stable logical node IDs allow corresponding nodes to be compared across versions.
4. **Selection and generation:** Users save named selections referencing node IDs and a specific document version. The selected source text is sent to a local Ollama model to generate structured QA test-case ideas.
5. **Retrieval and impact detection:** Generated tests retain their source version, node ID, and content hash. Retrieval endpoints compare the saved hash with the corresponding node in the latest imported version and report whether the source is stale.

## 3. Document Extraction and Structuring

The extraction pipeline uses the PDFs' native text layer rather than OCR. Extracted blocks preserve their source order and available layout metadata.

The hierarchy builder uses section numbering and heading/layout signals to associate content with section nodes. It avoids reordering sections solely by their numerical labels because the source may present sections out of numerical order.

When a child heading implies an intermediate parent that is absent from the source, the system records a warning rather than silently inventing a heading. Duplicate headings remain separate when their logical positions or parent sections differ.

Tables and complex visual layouts may be imperfectly represented by text-block extraction. The implementation preserves extracted text but does not claim to reconstruct every table or figure perfectly.

## 4. Node Identity and Content Hashing

Each logical node receives a deterministic ID based on its section identity. The same logical section can therefore be matched across versions even when its body text changes.

A SHA-256 hash is calculated from the node's heading and body content. Child-node content is not included in the parent's own content hash, allowing changes to a child section to be tracked independently.

The combination of stable IDs and content hashes supports:
- Matching logical sections across versions.
- Detecting changes to node-owned content.
- Preserving the relationship between generated test cases and their original source content.

## 5. Versioning and Change Detection

Each imported manual is stored as a separate document version. Historical nodes are retained rather than overwritten by a later import.

Version comparison matches nodes using stable logical IDs and categorizes them as:
- Added.
- Removed.
- Changed.
- Unchanged.

For changed nodes, the API can expose a lightweight text diff. This supports targeted review instead of requiring users to compare entire manuals manually.

## 6. Version-Pinned Selections

A saved selection contains a name and a reference to a specific document version. Its selected nodes are stored as node ID and version ID pairs.

This approach allows a saved selection to continue resolving to its original source text after a newer version is imported. Duplicate selection names are rejected within the same version to avoid ambiguous selection identity.

## 7. LLM-Powered Test-Case Generation

The generation service sends selected source text to the local Ollama `qwen3:8b` model. It requests three to five QA test-case ideas in JSON format.

Each generated case contains:
- Title.
- Objective.
- Preconditions.
- Test steps.
- Expected result.

The service parses the model response and validates the required fields and permitted number of cases. It retries after a generation or validation failure and returns an error if generation fails after the retry.

The generated output is persisted in SQLite and linked to the selection, source version, node ID, source content hash, and generation model.

LLM output is not guaranteed to be correct merely because it passes structural validation. Generated cases require review against the source requirements.

## 8. Retrieval and Staleness Detection

Generated cases can be retrieved by selection ID or node ID.

For each generated case, the API compares its saved source hash with the hash of the corresponding logical node in the latest imported version:
- Same hash: the source content matches.
- Different hash: the source content has changed.
- Missing node: the original logical node is absent from the latest version.

The API exposes an `is_stale` flag and, for selection-based retrieval, a reason.

This is a source-change indicator rather than a semantic judgment. A stale case may still be useful, while a non-stale case may still be incomplete or incorrect. Automatic regeneration is outside the current scope.

## 9. Testing Strategy

The automated test suite covers:
- PDF extraction behavior.
- Hierarchy construction and structural irregularities.
- Added, removed, changed, and unchanged nodes.
- Expected differences between the supplied manual versions.
- Same, different, and missing content hashes for staleness.
- API retrieval of saved test cases and handling of an unknown selection.

The API tests use an isolated in-memory SQLite database to avoid changing the development database. They do not call the external/local LLM service.

## 10. Limitations

- OCR is not implemented for scanned PDFs.
- Complex tables and figures may not be reconstructed perfectly from text blocks.
- Heading recognition relies on available numbering and layout signals and may require additional rules for unfamiliar manuals.
- Content-hash comparison does not establish semantic equivalence.
- Model-generated test cases require human review.
- Authentication, authorization, a user interface, production deployment, and automatic regeneration are outside the assignment prototype's scope.
