# Tri9T CT-200 Manual API
Install the dependencies.

pip install -r requirements.txt
Initialize and populate the SQLite database. Run these commands from the project root after activating the virtual environment.

python -m app.db.init_db
python -m app.db.import_manuals
A version-aware document processing and test-case generation API built with Python, FastAPI, SQLAlchemy, SQLite, and a locally hosted Ollama model.

## Overview

This project processes two versions of the CT-200 device manual. It extracts document text, organizes it into a hierarchy, tracks changes between versions, stores version-pinned selections, generates QA test-case ideas from selected content, and identifies generated tests whose source content has changed.

## Features

- Extract text and layout metadata from PDF manuals.
- Build a hierarchical document structure with stable logical node IDs.
- Store document versions and nodes in SQLite.
- Compare document versions and identify added, removed, changed, and unchanged nodes.
- Browse sections, retrieve nodes, and search document content.
- Save named selections pinned to a specific document version.
- Generate 3–5 QA test-case ideas using the local Ollama `qwen3:8b` model.
- Retrieve generated test cases by selection ID or node ID.
- Detect potential staleness by comparing the saved source content hash with the corresponding node in the latest version.
- Run automated tests for extraction, hierarchy construction, version comparison, staleness logic, and API behavior.

## Technology Stack

- Python
- FastAPI and Pydantic
- SQLAlchemy
- SQLite
- PyMuPDF
- Ollama (`qwen3:8b`)
- HTTPX
- pytest

## Project Structure

```text
tri9t-ct200/
├── app/
│   ├── db/
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── init_db.py
│   │   ├── import_manuals.py
│   │   └── check_db.py
│   ├── services/
│   │   ├── staleness.py
│   │   └── test_case_generator.py
│   ├── extract_pdf.py
│   ├── structure_manual.py
│   ├── build_hierarchy.py
│   ├── compare_versions.py
│   └── main.py
├── data/
├── extracted/
├── structured/
├── storage/
├── tests/
├── docs/
│   ├── approach.md
│   └── decision-log.md
└── README.md
```

## Setup

Run commands from the project root.

1. Create and activate a virtual environment if one does not already exist.

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install the dependencies used by the project.

   Install the project's required packages in the virtual environment. If a `requirements.txt` file is added, use:

   ```bash
   pip install -r requirements.txt
   ```

3. Ensure Ollama is installed and the model is available.

   ```bash
   ollama pull qwen3:8b
   ```

4. Initialize the database and import the structured manual versions using the project's database scripts, if the database has not already been populated.

## Run the API

```bash
uvicorn app.main:app --reload
```

Open the interactive API documentation at:

http://127.0.0.1:8000/docs

## Run Tests

```bash
python -m pytest -q
```

The current development test suite contains 18 passing tests.

## Example Workflow

1. Extract both manual PDFs and build their structured hierarchies.
2. Import both versions into SQLite.
3. Browse sections or compare v1 with v2.
4. Create a named selection referencing node IDs from a specific version.
5. Generate QA test-case ideas from the selection.
6. Retrieve the saved test cases by selection ID or node ID.
7. Review the staleness result to determine whether the original source content still matches the latest version.

## Staleness Limitations

Staleness is based on exact content-hash comparison, not semantic equivalence. A changed hash indicates that the source content differs; it does not prove that every generated test case is invalid. Conversely, an unchanged hash does not guarantee that a test case is complete or correct. Human review is still necessary.

The current implementation uses native PDF text extraction. OCR for scanned documents is not implemented. Test-case generation depends on a locally available Ollama service and model.

## Current Test Coverage

The suite covers PDF extraction, hierarchy construction and irregularities, version-diff behavior, staleness helper behavior, and selected API retrieval scenarios. Passing tests do not imply that every possible PDF layout, malformed model response, or production failure has been covered.

## Scope and Security

This is an internship assignment prototype. Authentication, authorization, a user interface, production deployment, and automatic regeneration of stale test cases are outside the current scope.
