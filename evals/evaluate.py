"""Deterministic contract checks. These do not measure a real model's reasoning quality."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from agent_app.config import Settings
from agent_app.main import create_app


def main() -> int:
    cases = [
        json.loads(line)
        for line in Path(__file__).with_name("cases.jsonl").read_text().splitlines()
    ]
    failures = 0
    with TemporaryDirectory() as temp:
        settings = Settings(
            _env_file=None,
            model_provider="demo",
            api_token="",
            database_path=Path(temp) / "eval.sqlite",
        )
        with TestClient(create_app(settings)) as client:
            for case in cases:
                response = client.post("/v1/runs", json={"message": case["message"]})
                result = response.json()
                passed = (
                    response.status_code == 200
                    and result["status"] == "completed"
                    and case["contains"] in result["output"]
                    and result["tool_events"]
                    == [{"name": case["tool"], "error": case.get("error")}]
                )
                failures += not passed
                print(json.dumps({"case": case["name"], "passed": passed}))
    print(f"{len(cases) - failures}/{len(cases)} demo contracts passed (not an LLM quality score).")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
