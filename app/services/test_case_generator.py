
import json
import httpx

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3:8b"


def generate_test_cases(source_text: str) -> list[dict]:
    prompt = f"""
You are a software QA engineer.

Use only the source text below to create 3 to 5 useful QA test case ideas.
Do not invent requirements that are not supported by the source.

Return ONLY valid JSON in this exact format:
{{
  "test_cases": [
    {{
      "title": "Short test title",
      "objective": "What is being tested",
      "preconditions": "Required initial state",
      "test_steps": "Numbered steps as a string",
      "expected_result": "Expected behavior based on the source"
    }}
  ]
}}

Source text:
{source_text}
"""

    for attempt in range(2):
        try:
            with httpx.Client(timeout=180.0) as client:
                response = client.post(
                    OLLAMA_URL,
                    json={
                        "model": MODEL_NAME,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                    },
                )
                response.raise_for_status()

            raw_text = response.json()["response"]
            result = json.loads(raw_text)
            cases = result.get("test_cases")

            if not isinstance(cases, list) or not 3 <= len(cases) <= 5:
                raise ValueError("Expected between 3 and 5 test cases.")

            required_fields = {
                "title",
                "objective",
                "preconditions",
                "test_steps",
                "expected_result",
            }

            for case in cases:
                if not isinstance(case, dict):
                    raise ValueError("Each test case must be a JSON object.")
                if not required_fields.issubset(case):
                    raise ValueError("A test case is missing required fields.")
                if any(
                    not isinstance(case[field], str) or not case[field].strip()
                    for field in required_fields
                ):
                    raise ValueError("Test case fields must be non-empty strings.")

            return cases

        except (httpx.HTTPError, KeyError, json.JSONDecodeError, ValueError) as exc:
            if attempt == 1:
                raise RuntimeError(
                    f"Test-case generation failed after 2 attempts: {exc}"
                ) from exc

    raise RuntimeError("Test-case generation failed.")
