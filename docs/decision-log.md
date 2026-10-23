# Technical Decision Log

## 1. PDF Extraction
**Decision:** Use PyMuPDF to extract text blocks from the supplied PDF manuals.

**Reason:** Both manuals contain extractable text, so native text extraction is sufficient for the current inputs.

**Limitation:** OCR is not implemented. Scanned documents may require an OCR fallback.

## 2. Source Order
**Decision:** Preserve the order in which content appears in the source document.

**Reason:** Some headings appear out of numerical order. Sorting them could change the original document structure.

## 3. Hierarchy Reconstruction
**Decision:** Reconstruct a parent-child hierarchy using section numbering and heading evidence, while recording structural warnings.

**Reason:** Missing intermediate headings must not be silently invented or incorrectly assigned.

## 4. Stable Node Identity
**Decision:** Use deterministic identifiers derived from section numbers.

**Reason:** Matching sections across document versions allows changes to be tracked without treating every section as new.

## 5. Content Hashing
**Decision:** Calculate SHA-256 hashes from each node's own heading and body text, excluding its children.

**Reason:** A change to one section's content can be distinguished from changes to its descendants.

## 6. Database
**Decision:** Use SQLite with SQLAlchemy for document versions, hierarchy nodes, selections, and generated test cases.

**Reason:** This provides persistent storage with a straightforward local setup.

## 7. Version-Pinned Selections
**Decision:** Store each selection with its document version and exact node-version pairs.

**Reason:** Previously saved selections must continue to resolve to the original version's content.

## 8. LLM Test-Case Generation
**Decision:** Use the local Ollama model `qwen3:8b` and validate the generated JSON output.

**Reason:** Local generation avoids requiring a paid hosted-model API for the demonstration.

**Failure handling:** Retry generation once when the response or structured output is invalid, then report an error.

## 9. Staleness Detection
**Decision:** Compare the source content hash saved with each generated test case against the corresponding node's hash in the latest version.

**Reason:** This identifies whether the source content has changed since generation.

**Limitation:** A changed hash indicates potential staleness; it does not prove that a test case is incorrect.

## 10. Testing
**Decision:** Use pytest for extraction, hierarchy, version comparison, staleness, and API behavior tests.

**Reason:** Automated tests help verify the core requirements and detect regressions.
