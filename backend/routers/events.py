from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from core.event_broadcaster import event_generator

router = APIRouter(prefix="/events", tags=["events"])

@router.get("/stream")
async def stream_events():
    """Server-Sent Events endpoint to stream real-time events to the dashboard."""
    return StreamingResponse(event_generator(), media_type="text/event-stream")
