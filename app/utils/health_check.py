from fastapi import APIRouter

router = APIRouter(tags=["utils"])


@router.get("/health_check")
async def health_check():
    return {"status": "OK"}
