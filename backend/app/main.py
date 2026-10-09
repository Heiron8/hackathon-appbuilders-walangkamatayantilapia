"""Lead-owned assembly. AI routes/validation integrate after LadlopezGit's review."""
import json
import re
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException

from shared.vocabulary import load_vocabulary

ROOT = Path(__file__).resolve().parents[2]


def create_app(frontend_dist=ROOT / "frontend" / "dist"):
    app = FastAPI(title="Tanaw", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.vocabulary = load_vocabulary()
    app.state.contracts = json.loads((ROOT / "shared" / "contracts.json").read_text(encoding="utf-8"))

    def error_response(status, code, message):
        return JSONResponse(status_code=status, content={
            "request_id": None, "error": {"code": code, "message": message},
        })

    @app.middleware("http")
    async def local_host_only(request: Request, call_next):
        # Reject DNS-rebinding hosts using the same JSON envelope as other errors.
        if not re.fullmatch(r"(?:127\.0\.0\.1|localhost)(?::[0-9]{1,5})?", request.headers.get("host", "")):
            return error_response(400, "invalid_request", "Local host required.")
        if request.method not in {"GET", "HEAD"}:
            origin = request.headers.get("origin")
            if origin is not None and origin not in {
                "http://127.0.0.1:5173", "http://localhost:5173",
                "http://127.0.0.1:8000", "http://localhost:8000",
            }:
                return error_response(403, "invalid_request", "Local application origin required.")
        return await call_next(request)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, exc: RequestValidationError):
        return error_response(422, "invalid_request", "Invalid request.")

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        return error_response(exc.status_code, "invalid_request", "Request could not be served.")

    @app.get("/api/health")
    async def health():
        # No model probing/inference: the backend lane replaces unknown after integration.
        return {"status": "ok", "vocabulary_version": app.state.vocabulary["version"],
                "ai": {"state": "unknown", "suggestions_enabled": False}}

    # Never allow missing API routes to fall through to the frontend static mount.
    @app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
    async def missing_api(path: str):
        return error_response(404, "invalid_request", "API route is not available.")

    # LadlopezGit's reviewed router must be included ABOVE the missing-api fallback.
    # No CORS is needed: Vite proxies /api and the final build shares this origin.
    frontend_dist = Path(frontend_dist)
    if (frontend_dist / "index.html").is_file():
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
    return app


app = create_app()
