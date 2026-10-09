"""Real loopback HTTP proof against checkpoint_app's synthetic vocabulary.

Run from backend: python -m tests.smoke_checkpoint --expect-ai ready --output <new.json>
Repeat with --expect-ai unavailable after stopping the owned Ollama process.
"""

import argparse
import asyncio
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import httpx

from app.validation.contracts import ModelCandidate
from app.validation.grammar import validate_candidate
from tests.fixtures import request_body


async def smoke(expected: str, output: Path) -> None:
    checks = []
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000", trust_env=False, timeout=7) as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["ai"] == {"state": expected, "suggestions_enabled": False}
        checks.append({"check": "health", "http": 200, "ai_state": expected})
        for ids in (["want", "eat", "apple"], ["not", "want", "eat", "apple"]):
            response = await client.post("/api/expand", json=request_body(ids))
            if expected == "ready":
                assert response.status_code == 200, response.status_code
                result = response.json()
                assert result["revision"] == 3 and result["request_id"] == request_body()["request_id"]
                assert result["status"] == "candidate" and result["vocabulary_version"] == "tanaw-v1"
                assert validate_candidate(ModelCandidate(source_card_ids=result["source_card_ids"], text=result["text"]), ids)
            else:
                assert response.status_code == 503
                assert response.json()["error"]["code"] == "ai_unavailable"
            checks.append({"check": "expand", "source_card_ids": ids, "http": response.status_code})
        response = await client.post("/api/expand", json=request_body(["water"]))
        assert response.status_code == 200 and response.json()["status"] == "unsupported"
        checks.append({"check": "unsupported_without_model", "http": 200})
        response = await client.post("/api/expand", json=request_body(["unknown"]))
        assert response.status_code == 422 and response.json()["error"]["code"] == "invalid_request"
        checks.append({"check": "unknown_id", "http": 422})
        response = await client.post("/api/expand", json=request_body(vocabulary_version="tanaw-v2"))
        assert response.status_code == 409 and response.json()["error"]["code"] == "vocabulary_mismatch"
        checks.append({"check": "version_mismatch", "http": 409})
    report = {"checked_at": datetime.now(timezone(timedelta(hours=8))).isoformat(),
              "scope": "real loopback HTTP; synthetic test vocabulary; network not checked",
              "checks": checks, "verdict": "PASS"}
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {len(checks)} loopback HTTP checks, AI {expected}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expect-ai", choices=("ready", "unavailable"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or not args.output.parent.is_dir():
        parser.error("Use a new report path in an existing directory.")
    asyncio.run(smoke(args.expect_ai, args.output))
