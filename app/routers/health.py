from fastapi import APIRouter

router = APIRouter(tags=["utils"])


@router.get("/health")
async def health():
    """Check if the application is healthy.

    This endpoint can be used by monitoring tools to verify that
    the application is running and responding to requests.
    """

    # TODO: Add actual health checks (e.g., Redis connection, memory usage)
    return {"status": "OK"}
