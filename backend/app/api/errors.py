"""Opt-in app handlers for Lead-owned assembly; preserve HTTP status/headers."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

ERRORS = {
    "invalid_request": (422, "The sentence request is invalid."),
    "vocabulary_mismatch": (409, "Sentence assistance needs a matching vocabulary version."),
    "request_too_large": (413, "The sentence request exceeds the input limit."),
    "ai_unavailable": (503, "Sentence assistance is unavailable. You can still speak selected cards."),
    "ai_busy": (429, "Sentence assistance is busy. You can still speak selected cards."),
    "ai_timeout": (504, "Sentence assistance timed out. You can still speak selected cards."),
    "invalid_ai_output": (502, "Sentence assistance could not preserve the selected words."),
}


def error_response(code: str, request_id: str | None = None, *, status_code: int | None = None,
                   headers: dict[str, str] | None = None, message: str | None = None) -> JSONResponse:
    status, default_message = ERRORS[code]
    return JSONResponse(status_code=status if status_code is None else status_code, headers=headers,
                        content={"request_id": request_id,
                                 "error": {"code": code, "message": default_message if message is None else message}})


def install_error_handlers(app: FastAPI) -> None:
    """Explicitly register this in production main.py after the Lead reviews it.

    HTTP details and validation inputs are never returned. Register the Starlette
    base exception so both framework 404/405 and FastAPI HTTP exceptions use it.
    This does not change routing, static mounts or the missing-API fallback.
    """
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        return error_response("invalid_request", status_code=exc.status_code, headers=exc.headers,
                              message="Request could not be served.")

    async def invalid_request(request: Request, exc: RequestValidationError) -> JSONResponse:
        return error_response("invalid_request")

    app.add_exception_handler(HTTPException, http_error)
    app.add_exception_handler(RequestValidationError, invalid_request)
