import hashlib
import hmac
import time
import uuid
from typing import Optional, Dict, Any, Callable, Awaitable
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import json
import logging
from threading import Lock

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EventStatus(Enum):
    """Status of webhook event processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WebhookEvent:
    """Represents a webhook event."""
    event_id: str
    event_type: str
    payload: Dict[str, Any]
    timestamp: datetime
    signature: str
    status: EventStatus = EventStatus.PENDING
    retry_count: int = 0
    last_retry: Optional[datetime] = None


@dataclass
class WebhookConfig:
    """Configuration for webhook receiver."""
    secret_key: str
    signature_header: str = "X-Webhook-Signature"
    signature_algorithm: str = "sha256"
    max_retries: int = 3
    retry_delay: int = 60
    deduplication_window: int = 3600
    max_queue_size: int = 10000
    worker_count: int = 5


class DeduplicationCache:
    """Thread-safe cache for deduplicating webhook events."""
    
    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize deduplication cache.
        
        Args:
            ttl_seconds: Time-to-live for cached entries in seconds
        """
        self._cache: Dict[str, datetime] = {}
        self._lock = Lock()
        self._ttl_seconds = ttl_seconds
    
    def is_duplicate(self, event_id: str) -> bool:
        """
        Check if an event ID has been seen before.
        
        Args:
            event_id: Unique identifier for the event
            
        Returns:
            True if event is a duplicate, False otherwise
        """
        with self._lock:
            self._cleanup_expired()
            
            if event_id in self._cache:
                return True
            
            self._cache[event_id] = datetime.utcnow()
            return False
    
    def _cleanup_expired(self) -> None:
        """Remove expired entries from cache."""
        cutoff_time = datetime.utcnow() - timedelta(seconds=self._ttl_seconds)
        expired_keys = [
            key for key, timestamp in self._cache.items()
            if timestamp < cutoff_time
        ]
        for key in expired_keys:
            del self._cache[key]
    
    def clear(self) -> None:
        """Clear all entries from cache."""
        with self._lock:
            self._cache.clear()


class SignatureValidator:
    """Validates HMAC signatures for webhook requests."""
    
    def __init__(self, secret_key: str, algorithm: str = "sha256"):
        """
        Initialize signature validator.
        
        Args:
            secret_key: Secret key for HMAC validation
            algorithm: Hash algorithm to use (default: sha256)
        """
        self.secret_key = secret_key.encode()
        self.algorithm = algorithm
    
    def validate(self, payload: bytes, signature: str) -> bool:
        """
        Validate HMAC signature for given payload.
        
        Args:
            payload: Raw payload bytes
            signature: Signature to validate
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            expected_signature = self._compute_signature(payload)
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            logger.error(f"Signature validation error: {e}")
            return False
    
    def _compute_signature(self, payload: bytes) -> str:
        """
        Compute HMAC signature for payload.
        
        Args:
            payload: Raw payload bytes
            
        Returns:
            Computed signature as hex string
        """
        hash_func = getattr(hashlib, self.algorithm)
        return hmac.new(self.secret_key, payload, hash_func).hexdigest()


class EventProcessor:
    """Processes webhook events asynchronously with retry logic."""
    
    def __init__(self, config: WebhookConfig):
        """
        Initialize event processor.
        
        Args:
            config: Webhook configuration
        """
        self.config = config
        self.handlers: Dict[str, Callable[[WebhookEvent], Awaitable[None]]] = {}
        self._processing_events: Dict[str, WebhookEvent] = {}
        self._lock = asyncio.Lock()
    
    def register_handler(
        self,
        event_type: str,
        handler: Callable[[WebhookEvent], Awaitable[None]]
    ) -> None:
        """
        Register a handler for specific event type.
        
        Args:
            event_type: Type of event to handle
            handler: Async function to process the event
        """
        self.handlers[event_type] = handler
        logger.info(f"Registered handler for event type: {event_type}")
    
    async def process_event(self, event: WebhookEvent) -> bool:
        """
        Process a webhook event with retry logic.
        
        Args:
            event: Webhook event to process
            
        Returns:
            True if processing succeeded, False otherwise
        """
        async with self._lock:
            self._processing_events[event.event_id] = event
        
        try:
            event.status = EventStatus.PROCESSING
            
            handler = self.handlers.get(event.event_type)
            if not handler:
                logger.warning(f"No handler registered for event type: {event.event_type}")
                event.status = EventStatus.FAILED
                return False
            
            await handler(event)
            event.status = EventStatus.COMPLETED
            logger.info(f"Successfully processed event: {event.event_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing event {event.event_id}: {e}")
            event.status = EventStatus.FAILED
            
            if event.retry_count < self.config.max_retries:
                event.retry_count += 1
                event.last_retry = datetime.utcnow()
                event.status = EventStatus.PENDING
                logger.info(
                    f"Scheduling retry {event.retry_count}/{self.config.max_retries} "
                    f"for event: {event.event_id}"
                )
                asyncio.create_task(self._retry_event(event))
            
            return False
            
        finally:
            async with self._lock:
                if event.status == EventStatus.COMPLETED:
                    self._processing_events.pop(event.event_id, None)
    
    async def _retry_event(self, event: WebhookEvent) -> None:
        """
        Retry processing an event after delay.
        
        Args:
            event: Event to retry
        """
        await asyncio.sleep(self.config.retry_delay)
        await self.process_event(event)
    
    def get_processing_status(self, event_id: str) -> Optional[EventStatus]:
        """
        Get current status of an event.
        
        Args:
            event_id: Event identifier
            
        Returns:
            Event status or None if not found
        """
        event = self._processing_events.get(event_id)
        return event.status if event else None


class WebhookReceiver:
    """Main webhook receiver with validation, deduplication, and async processing."""
    
    def __init__(self, config: WebhookConfig):
        """
        Initialize webhook receiver.
        
        Args:
            config: Webhook configuration
        """
        self.config = config
        self.validator = SignatureValidator(config.secret_key, config.signature_algorithm)
        self.dedup_cache = DeduplicationCache(config.deduplication_window)
        self.processor = EventProcessor(config)
        self.event_queue: asyncio.Queue[WebhookEvent] = asyncio.Queue(
            maxsize=config.max_queue_size
        )
        self._workers: list[asyncio.Task] = []
        self._running = False
    
    def register_event_handler(
        self,
        event_type: str,
        handler: Callable[[WebhookEvent], Awaitable[None]]
    ) -> None:
        """
        Register handler for specific event type.
        
        Args:
            event_type: Type of event to handle
            handler: Async function to process the event
        """
        self.processor.register_handler(event_type, handler)
    
    async def receive_webhook(
        self,
        payload: bytes,
        signature: str,
        event_type: str,
        event_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Receive and validate a webhook request.
        
        Args:
            payload: Raw payload bytes
            signature: HMAC signature from request header
            event_type: Type of webhook event
            event_id: Optional unique event identifier
            
        Returns:
            Response dictionary with status and message
        """
        if not self.validator.validate(payload, signature):
            logger.warning("Invalid webhook signature")
            return {
                "status": "error",
                "message": "Invalid signature"
            }
        
        try:
            payload_dict = json.loads(payload.decode())
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON payload: {e}")
            return {
                "status": "error",
                "message": "Invalid JSON payload"
            }
        
        if not event_id:
            event_id = payload_dict.get("id", str(uuid.uuid4()))
        
        if self.dedup_cache.is_duplicate(event_id):
            logger.info(f"Duplicate event received: {event_id}")
            return {
                "status": "success",
                "message": "Event already processed",
                "event_id": event_id
            }
        
        event = WebhookEvent(
            event_id=event_id,
            event_type=event_type,
            payload=payload_dict,
            timestamp=datetime.utcnow(),
            signature=signature
        )
        
        try:
            await asyncio.wait_for(
                self.event_queue.put(event),
                timeout=5.0
            )
            logger.info(f"Queued event: {event_id}")
            return {
                "status": "success",
                "message": "Event queued for processing",
                "event_id": event_id
            }
        except asyncio.TimeoutError:
            logger.error("Event queue full, rejecting webhook")
            return {
                "status": "error",
                "message": "Queue full, try again later"
            }
    
    async def start_workers(self) -> None:
        """Start background workers to process events."""
        if self._running:
            logger.warning("Workers already running")
            return
        
        self._running = True
        self._workers = [
            asyncio.create_task(self._worker(i))
            for i in range(self.config.worker_count)
        ]
        logger.info(f"Started {self.config.worker_count} workers")
    
    async def stop_workers(self) -> None:
        """Stop all background workers gracefully."""
        if not self._running:
            return
        
        self._running = False
        
        for worker in self._workers:
            worker.cancel()
        
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        logger.info("All workers stopped")
    
    async def _worker(self, worker_id: int) -> None:
        """
        Background worker that processes events from queue.
        
        Args:
            worker_id: Identifier for this worker
        """
        logger.info(f"Worker {worker_id} started")
        
        while self._running:
            try:
                event = await asyncio.wait_for(
                    self.event_queue.get(),
                    timeout=1.0
                )
                
                logger.debug(f"Worker {worker_id} processing event: {event.event_id}")
                await self.processor.process_event(event)
                self.event_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def wait_for_completion(self) -> None:
        """Wait for all queued events to be processed."""
        await self.event_queue.join()
    
    def get_queue_size(self) -> int:
        """
        Get current queue size.
        
        Returns:
            Number of events in queue
        """
        return self.event_queue.qsize()


async def example_usage():
    """Example usage of the webhook receiver."""
    
    config = WebhookConfig(
        secret_key="your-secret-key-here",
        signature_header="X-Webhook-Signature",
        max_retries=3,
        retry_delay=5,
        worker_count=3
    )
    
    receiver = WebhookReceiver(config)
    
    async def handle_order_event(event: WebhookEvent) -> None:
        """Example handler for order events."""
        logger.info(f"Processing order event: {event.event_id}")
        logger.info(f"Payload: {event.payload}")
        await asyncio.sleep(0.1)
    
    async def handle_payment_event(event: WebhookEvent) -> None:
        """Example handler for payment events."""
        logger.info(f"Processing payment event: {event.event_id}")
        logger.info(f"Payload: {event.payload}")
        await asyncio.sleep(0.1)
    
    receiver.register_event_handler("order.created", handle_order_event)
    receiver.register_event_handler("payment.completed", handle_payment_event)
    
    await receiver.start_workers()
    
    payload = json.dumps({"id": "evt_123", "data": "test"}).encode()
    validator = SignatureValidator(config.secret_key)
    signature = validator._compute_signature(payload)
    
    result = await receiver.receive_webhook(
        payload=payload,
        signature=signature,
        event_type="order.created"
    )
    
    logger.info(f"Webhook result: {result}")
    
    await receiver.wait_for_completion()
    await receiver.stop_workers()


if __name__ == "__main__":
    asyncio.run(example_usage())