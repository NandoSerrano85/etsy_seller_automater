import asyncio
import json
import logging
import time
import uuid
from typing import Dict, Optional, AsyncGenerator
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class ProgressUpdate:
    """Progress update data structure"""
    step: int
    total_steps: int
    message: str
    progress_percent: float
    elapsed_time: float
    timestamp: datetime

class ProgressManager:
    """Manages upload progress tracking with SSE support"""

    def __init__(self):
        self._progress_data: Dict[str, ProgressUpdate] = {}
        self._subscribers: Dict[str, list] = {}
        self._start_times: Dict[str, float] = {}

    def create_session(self) -> str:
        """Create a new progress tracking session"""
        session_id = str(uuid.uuid4())
        self._start_times[session_id] = time.time()
        self._subscribers[session_id] = []
        logging.info(f"Created progress session: {session_id}")
        return session_id

    def update_progress(self, session_id: str, step: int, total_steps: int, message: str):
        """Update progress for a session"""
        if session_id not in self._start_times:
            logging.warning(f"Progress session not found: {session_id}")
            return

        start_time = self._start_times[session_id]
        elapsed_time = time.time() - start_time
        progress_percent = (step / total_steps) * 100 if total_steps > 0 else 0

        update = ProgressUpdate(
            step=step,
            total_steps=total_steps,
            message=message,
            progress_percent=progress_percent,
            elapsed_time=elapsed_time,
            timestamp=datetime.now()
        )

        self._progress_data[session_id] = update
        logging.info(f"Progress update [{session_id}]: Step {step}/{total_steps} - {message} ({progress_percent:.1f}%)")

        # Notify all subscribers for this session
        self._notify_subscribers(session_id, update)

    def _notify_subscribers(self, session_id: str, update: ProgressUpdate):
        """Notify all subscribers of a progress update"""
        if session_id in self._subscribers:
            # Create a copy of subscribers list to avoid modification during iteration
            subscribers = self._subscribers[session_id].copy()
            for queue in subscribers:
                try:
                    queue.put_nowait(update)
                except asyncio.QueueFull:
                    logging.warning(f"Progress queue full for session {session_id}")
                except Exception as e:
                    logging.error(f"Error notifying subscriber: {e}")

    async def subscribe(self, session_id: str) -> AsyncGenerator[str, None]:
        """Subscribe to progress updates for a session via SSE"""
        if session_id not in self._subscribers:
            logging.warning(f"Cannot subscribe to non-existent session: {session_id}")
            return

        queue = asyncio.Queue(maxsize=100)
        self._subscribers[session_id].append(queue)

        try:
            # Send current progress if available
            if session_id in self._progress_data:
                current_progress = self._progress_data[session_id]
                yield f"data: {json.dumps(asdict(current_progress), default=str)}\n\n"

            # Listen for new updates
            while True:
                try:
                    update = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(asdict(update), default=str)}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f"data: {json.dumps({'type': 'keepalive', 'timestamp': datetime.now()}, default=str)}\n\n"
                except Exception as e:
                    logging.error(f"Error in progress subscription: {e}")
                    break

        finally:
            # Clean up subscription
            if session_id in self._subscribers and queue in self._subscribers[session_id]:
                self._subscribers[session_id].remove(queue)
                logging.info(f"Removed subscriber from session: {session_id}")

    def complete_session(self, session_id: str, success: bool = True, final_message: str = "Upload completed"):
        """Mark a session as completed"""
        if session_id in self._start_times:
            total_steps = self._progress_data.get(session_id, ProgressUpdate(0, 4, "", 0, 0, datetime.now())).total_steps

            # Send final progress update
            self.update_progress(
                session_id=session_id,
                step=total_steps,
                total_steps=total_steps,
                message=final_message
            )

            # Clean up after a delay to allow final messages to be sent
            asyncio.create_task(self._cleanup_session_delayed(session_id))

    async def _cleanup_session_delayed(self, session_id: str):
        """Clean up session data after a delay"""
        await asyncio.sleep(5)  # Wait 5 seconds before cleanup
        self.cleanup_session(session_id)

    def cleanup_session(self, session_id: str):
        """Clean up session data"""
        self._progress_data.pop(session_id, None)
        self._start_times.pop(session_id, None)

        # Close all remaining subscribers
        if session_id in self._subscribers:
            for queue in self._subscribers[session_id]:
                try:
                    queue.put_nowait(None)  # Signal end of stream
                except:
                    pass
            del self._subscribers[session_id]

        logging.info(f"Cleaned up progress session: {session_id}")

    def get_progress(self, session_id: str) -> Optional[ProgressUpdate]:
        """Get current progress for a session"""
        return self._progress_data.get(session_id)

# Global progress manager instance
progress_manager = ProgressManager()