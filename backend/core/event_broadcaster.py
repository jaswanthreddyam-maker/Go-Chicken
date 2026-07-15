import asyncio
import json
import logging
from typing import Dict, Any, Set
from datetime import datetime

logger = logging.getLogger("go_chicken.event_broadcaster")

# In-memory pubsub for SSE
_connected_clients: Set[asyncio.Queue] = set()

async def broadcast_event(event_type: str, payload: Dict[str, Any]):
    """
    Broadcasts a typed event to all connected SSE clients.
    event_type: e.g., 'ORDER_CONFIRMED', 'INVENTORY_CHANGED', 'AI_EXTRACTION'
    payload: dict of relevant data.
    """
    event = {
        "type": event_type,
        "data": payload,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    # Push to all connected queues
    dead_queues = set()
    for q in _connected_clients:
        try:
            q.put_nowait(event)
        except asyncio.QueueFull:
            dead_queues.add(q)
            
    for q in dead_queues:
        _connected_clients.remove(q)

async def event_generator():
    """Generator for FastAPI StreamingResponse yielding SSE strings."""
    q = asyncio.Queue()
    _connected_clients.add(q)
    try:
        while True:
            event = await q.get()
            yield f"data: {json.dumps(event)}\n\n"
    except asyncio.CancelledError:
        _connected_clients.remove(q)
        raise
    except Exception as e:
        logger.error(f"SSE generator error: {e}")
        _connected_clients.remove(q)
        raise
