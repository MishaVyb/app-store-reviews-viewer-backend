from fastapi import APIRouter

app_store_reviews = APIRouter(prefix="/reviews", tags=["App Store Reviews"])

# TODO

monitoring = APIRouter(prefix="", tags=["Monitoring"])


@monitoring.get("/health")
async def health() -> None:
    return None
