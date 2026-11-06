from fastapi import APIRouter, Request
from fastapi.responses import Response

router = APIRouter()


@router.api_route("/health", methods=["GET", "HEAD"], tags=["health"])
@router.api_route("/ping", methods=["GET", "HEAD"], include_in_schema=False)
async def health(request: Request) -> dict[str, str] | Response:
    if request.method == "HEAD":
        return Response(status_code=200)
    return {"status": "ok"}
