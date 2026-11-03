from fastapi import APIRouter, Request
from fastapi.responses import Response

router = APIRouter()


@router.api_route("/health", methods=["GET", "HEAD"], tags=["health"])
async def health(request: Request) -> dict[str, str] | Response:
    if request.method == "HEAD":
        return Response(status_code=200)
    return {"status": "ok"}
