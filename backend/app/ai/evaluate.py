"""Explicit setup/benchmark command; never invoked by an application request.

Run from backend: python -m app.ai.evaluate --output <new-report.json>
It warms the already installed model, then runs 30 real bounded adapter calls.
Only public fixture IDs/outcomes/timings are recorded, never generated text.
"""

import argparse
import asyncio
from datetime import datetime, timedelta, timezone
from importlib.metadata import version
import json
import math
from pathlib import Path
from time import perf_counter

import httpx

from .ollama import BASE_URL, InferenceError, OllamaRuntime, chat_request
from ..validation.contracts import ModelCandidate
from ..validation.grammar import validate_candidate

FIXTURES = (
    ("want", "eat", "apple"), ("not", "want", "eat", "apple"),
    ("i", "want", "drink", "water"), ("i", "not", "want", "drink", "milk"),
    ("want", "banana"), ("not", "want", "toy"),
    ("i", "want", "ball"), ("i", "not", "want", "rice"),
    ("want", "drink", "juice"), ("not", "want", "eat", "bread"),
    ("i", "want", "eat", "banana"), ("i", "not", "want", "water"),
)


def percentile(values: list[float], fraction: float) -> float:
    return sorted(values)[max(0, math.ceil(len(values) * fraction) - 1)]


async def evaluate(output: Path, model: str, calls: int) -> bool:
    report = {
        "checked_at": datetime.now(timezone(timedelta(hours=8))).isoformat(),
        "model": model,
        "network_scope": "network not checked by this benchmark; disconnected restart NOT VERIFIED",
        "implementation_scope": "real local runtime/adapter; production app assembly not integrated",
        "packages": {name: version(name) for name in ("fastapi", "pydantic", "httpx", "uvicorn")},
        "warm_calls": [],
    }
    runtime = OllamaRuntime(model=model)
    try:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=120, trust_env=False,
                                     follow_redirects=False) as client:
            for path, key in (("/api/version", "runtime"), ("/api/tags", "installed_models")):
                response = await client.get(path)
                response.raise_for_status()
                report[key] = response.json()
            # Loading weights alone does not warm first-generation CUDA graphs.
            # Run a complete fixture during explicit setup, outside the product deadline.
            started = perf_counter()
            async with asyncio.timeout(120):
                response = await client.post("/api/chat", json=chat_request(model, list(FIXTURES[0])))
            response.raise_for_status()
            report["setup_load_ms"] = round((perf_counter() - started) * 1000, 2)
            report["setup_load_duration_ns"] = response.json().get("load_duration")
            report["setup_kind"] = "complete fixture inference, including load and first generation"
            candidate = ModelCandidate.model_validate_json(response.json()["message"]["content"])
            report["setup_candidate_valid"] = validate_candidate(candidate, list(FIXTURES[0]))
            if not report["setup_candidate_valid"]:
                return False
            for index in range(calls):
                ids = list(FIXTURES[index % len(FIXTURES)])
                started = perf_counter()
                try:
                    await runtime.expand(ids)
                    outcome = "candidate"
                except InferenceError as exc:
                    outcome = exc.code
                entry = {"fixture": index % len(FIXTURES), "source_card_ids": ids,
                         "outcome": outcome, "duration_ms": round((perf_counter() - started) * 1000, 2)}
                report["warm_calls"].append(entry)
                print(f"call={index + 1} fixture={entry['fixture']} outcome={outcome} duration_ms={entry['duration_ms']}",
                      flush=True)
            response = await client.get("/api/ps")
            response.raise_for_status()
            report["loaded_model_memory"] = response.json()
        timings = [entry["duration_ms"] for entry in report["warm_calls"]]
        success = sum(entry["outcome"] == "candidate" for entry in report["warm_calls"]) / calls
        # Each of the twelve fixtures also needs to pass, not just aggregate repetitions.
        fixture_success = sum(any(entry["fixture"] == index and entry["outcome"] == "candidate"
                                  for entry in report["warm_calls"]) for index in range(len(FIXTURES))) / len(FIXTURES)
        report["summary"] = {"calls": calls, "supported_success_rate": success,
            "supported_fixture_success_rate": fixture_success,
            "p50_ms": percentile(timings, 0.5), "p95_ms": percentile(timings, 0.95),
            "warm_quality_and_latency_pass": success >= 0.9 and fixture_success >= 0.9 and percentile(timings, 0.95) <= 3000,
            "overall_feasibility": "NOT ACCEPTED: disconnected proof and independent review pending"}
        return report["summary"]["warm_quality_and_latency_pass"]
    except (httpx.HTTPError, ValueError, TimeoutError, KeyError, TypeError) as exc:
        report["setup_error"] = type(exc).__name__
        return False
    finally:
        await runtime.aclose()
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default="qwen3:1.7b")
    parser.add_argument("--calls", type=int, default=30)
    args = parser.parse_args()
    if args.calls < 30:
        parser.error("At least 30 warm calls are required.")
    if args.output.exists() or not args.output.parent.is_dir():
        parser.error("Use a new report path in an existing directory; existing evidence is preserved.")
    raise SystemExit(0 if asyncio.run(evaluate(args.output, args.model, args.calls)) else 1)


if __name__ == "__main__":
    main()
