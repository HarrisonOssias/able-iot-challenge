from fastapi import APIRouter
from schemas.response import StatusResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=StatusResponse)
async def health():
    return StatusResponse()
