import hashlib
import hmac
import time
import uuid
from typing import Optional, Dict, Any, Callable, Awaitable, Set, Union
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import json
import logging

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
    raw_payload: bytes
    status: EventStatus = EventStatus.PENDING
    retry_count: int = 0
    last_retry: Optional[datetime] = None


@dataclass
class WebhookConfig:
    """Configuration for webhook receiver."""
    secret_key: Union[str, bytes]
    signature_header: str = "X-Webhook-Signature"
    signature_algorithm: str = "sha256"
    signature_format: str = "hex"
    max_retries: int = 3
    retry_delay: int = 60
    deduplication_window: int = 3600
    max_queue_size: int = 10000
    worker_count: int = 5
    max_payload_size: int = 10 * 1024 * 1024
    handler_timeout: int = 300
    shutdown_timeout: int = 30


class DeduplicationCache:
    """Async-safe cache for deduplicating webhook events."""
    
    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize deduplication cache.
        
        Args:
            ttl_seconds: Time-to-live for cached entries in seconds
        """
        self._cache: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()
        self._ttl_seconds = ttl_seconds
    
    async def is_duplicate(self, event_id: str) -> bool:
        """
        Check if an event ID has been seen before.
        
        Args:
            event_id: Unique identifier for the event
            
        Returns:
            True if event is a duplicate, False otherwise
        """
        async with self._lock:
            await self._cleanup_expired()
            
            if event_id in self._cache:
                return True
            
            self._cache[event_id] = datetime.now(timezone.utc)
            return False
    
    async def _cleanup_expired(self) -> None:
        """Remove expired entries from cache."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=self._ttl_seconds)
        expired_keys = [
            key for key, timestamp in self._cache.items()
            if timestamp < cutoff_time
        ]
        for key in expired_keys:
            del self._cache[key]
    
    async def clear(self) -> None:
        """Clear all entries from cache."""
        async with self._lock:
            self._cache.clear()


class SignatureValidator:
    """Validates HMAC signatures for webhook requests."""
    
    SUPPORTED_ALGORITHMS = {'sha1', 'sha256', 'sha384', 'sha512'}
    SUPPORTED_FORMATS = {'hex', 'base64'}
    MIN_SECRET_LENGTH = 16
    
    def __init__(
        self,
        secret_key: Union[str, bytes],
        algorithm: str = "sha256",
        signature_format: str = "hex"
    ):
        """
        Initialize signature validator.
        
        Args:
            secret_key: Secret key for HMAC validation
            algorithm: Hash algorithm to use (default: sha256)
            signature_format: Format of signature ('hex' or 'base64')
        """
        if isinstance(secret_key, str):
            secret_key = secret_key.encode()
        
        if len(secret_key) < self.MIN_SECRET_LENGTH:
            logger.warning(
                f"Secret key length ({len(secret_key)}) is below recommended "
                f"minimum ({self.MIN_SECRET_LENGTH} bytes)"
            )
        
        if algorithm not in self.SUPPORTED_ALGORITHMS:
            raise ValueError(
                f"Unsupported algorithm: {algorithm}. "
                f"Supported: {self.SUPPORTED_ALGORITHMS}"
            )
        
        if signature_format not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported signature format: {signature_format}. "
                f"Supported: {self.SUPPORTED_FORMATS}"
            )
        
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.signature_format = signature_format
    
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
        except (ValueError, TypeError) as e:
            logger.error(f"Signature validation error: {e}")
            return False
    
    def _compute_signature(self, payload: bytes) -> str:
        """
        Compute HMAC signature for payload.
        
        Args:
            payload: Raw payload bytes
            
        Returns:
            Computed signature as hex or base64 string
        """
        hash_func = getattr(hashlib, self.algorithm)
        mac = hmac.new(self.secret_key, payload, hash_func)
        
        if self.signature_format == 'hex':
            return mac.hexdigest()
        elif self.signature_format == 'base64':
            import base64
            return base64.b64encode(mac.digest()).decode('ascii')
        else:
            raise ValueError(f"Unsupported signature format: {self.signature_format}")


class CircuitBreaker:
    """Circuit breaker to prevent overwhelming failing handlers."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 1
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            half_open_max_calls: Max calls allowed in half-open state
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self._failure_count: Dict[str, int] = defaultdict(int)
        self._last_failure_time: Dict[str, datetime] = {}
        self._state: Dict[str, str] = defaultdict(lambda: "closed")
        self._half_open_calls: Dict[str, int] = defaultdict(int)
        self._lock = asyncio.Lock()
    
    async def call(
        self,
        event_type: str,
        func: Callable[[], Awaitable[None]]
    ) -> bool:
        """
        Execute function through circuit breaker.
        
        Args:
            event_type: Type of event being processed
            func: Async function to execute
            
        Returns:
            True if execution succeeded, False otherwise
        """
        async with self._lock:
            state = self._state[event_type]
            
            if state == "open":
                if self._should_attempt_reset(event_type):
                    self._state[event_type] = "half_open"
                    self._half_open_calls[event_type] = 0
                else:
                    logger.warning(f"Circuit breaker open for {event_type}")
                    return False
            
            if state == "half_open":
                if self._half_open_calls[event_type] >= self.half_open_max_calls:
                    logger.warning(f"Circuit breaker half-open limit reached for {event_type}")
                    return False
                self._half_open_calls[event_type] += 1
        
        try:
            await func()
            async with self._lock:
                self._on_success(event_type)
            return True
        except Exception as e:
            async with self._lock:
                self._on_failure(event_type)
            raise
    
    def _should_attempt_reset(self, event_type: str) -> bool:
        """Check if enough time has passed to attempt reset."""
        last_failure = self._last_failure_time.get(event_type)
        if not last_failure:
            return True
        
        elapsed = (datetime.now(timezone.utc) - last_failure).total_seconds()
        return elapsed >= self.recovery_timeout
    
    def _on_success(self, event_type: str) -> None:
        """Handle successful execution."""
        self._failure_count[event_type] = 0
        self._state[event_type] = "closed"
        self._half_open_calls[event_type] = 0
    
    def _on_failure(self, event_type: str) -> None:
        """Handle failed execution."""
        self._failure_count[event_type] += 1
        self._last_failure_time[event_type] = datetime.now(timezone.utc)
        
        if self._failure_count[event_type] >= self.failure_threshold:
            self._state[event_type] = "open"
            logger.error(
                f"Circuit breaker opened for {event_type} after "
                f"{self._failure_count[event_type]} failures"
            )


class EventProcessor:
    """Processes webhook events asynchronously with retry logic."""
    
    def __init__(self, config: WebhookConfig, validator: SignatureValidator):
        """
        Initialize event processor.
        
        Args:
            config: Webhook configuration
            validator: Signature validator for re-validation on retry
        """
        self.config = config
        self.validator = validator
        self.handlers: Dict[str, Callable[[WebhookEvent], Awaitable[None]]] = {}
        self._processing_events: Dict[str, WebhookEvent] = {}
        self._retry_tasks: Set[asyncio.Task] = set()
        self._lock = asyncio.Lock()
        self._circuit_breaker = CircuitBreaker()
    
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
            
            if event.retry_count > 0:
                if not self.validator.validate(event.raw_payload, event.signature):
                    logger.error(
                        f"Signature validation failed on retry for event: {event.event_id}"
                    )
                    event.status = EventStatus.FAILED
                    await self._cleanup_event(event.event_id)
                    return False
            
            handler = self.handlers.get(event.event_type)
            if not handler:
                logger.warning(f"No handler registered for event type: {event.event_type}")
                event.status = EventStatus.FAILED
                await self._cleanup_event(event.event_id)
                return False
            
            async def execute_handler():
                await asyncio.wait_for(
                    handler(event),
                    timeout=self.config.handler_timeout
                )
            
            await self._circuit_breaker.call(event.event_type, execute_handler)
            
            event.status = EventStatus.COMPLETED
            logger.info(f"Successfully processed event: {event.event_id}")
            await self._cleanup_event(event.event_id)
            return True
            
        except asyncio.TimeoutError:
            logger.error(
                f"Handler timeout ({self.config.handler_timeout}s) "
                f"for event {event.event_id}"
            )
            event.status = EventStatus.FAILED
            await self._handle_retry(event)
            return False
            
        except Exception as e:
            logger.error(f"Error processing event {event.event_id}: {e}")
            event.status = EventStatus.FAILED
            await self._handle_retry(event)
            return False
    
    async def _handle_retry(self, event: WebhookEvent) -> None:
        """
        Handle retry logic for failed event.
        
        Args:
            event: Failed event to potentially retry
        """
        if event.retry_count < self.config.max_retries:
            event.retry_count += 1
            event.last_retry = datetime.now(timezone.utc)
            event.status = EventStatus.PENDING
            
            delay = self.config.retry_delay * (2 ** (event.retry_count - 1))
            jitter = delay * 0.1
            delay = delay + (hash(event.event_id) % int(jitter * 100)) / 100
            
            logger.info(
                f"Scheduling retry {event.retry_count}/{self.config.max_retries} "
                f"for event: {event.event_id} in {delay:.1f}s"
            )
            
            task = asyncio.create_task(self._retry_event(event, delay))
            self._retry_tasks.add(task)
            task.add_done_callback(self._retry_tasks.discard)
        else:
            logger.error(
                f"Event {event.event_id} failed after {self.config.max_retries} retries"
            )
            await self._cleanup_event(event.event_id)
    
    async def _retry_event(self, event: WebhookEvent, delay: float) -> None:
        """
        Retry processing an event after delay.
        
        Args:
            event: Event to retry
            delay: Delay in seconds before retry
        """
        try:
            await asyncio.sleep(delay)
            await self.process_event(event)
        except asyncio.CancelledError:
            logger.info(f"Retry cancelled for event: {event.event_id}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in retry for event {event.event_id}: {e}")
    
    async def _cleanup_event(self, event_id: str) -> None:
        """
        Remove event from processing tracking.
        
        Args:
            event_id: ID of event to clean up
        """
        async with self._lock:
            self._processing_events.pop(event_id, None)
    
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
    
    async def cancel_all_retries(self) -> None:
        """Cancel all pending retry tasks."""
        for task in self._retry_tasks:
            task.cancel()
        
        if self._retry_tasks:
            await asyncio.gather(*self._retry_tasks, return_exceptions=True)
        
        self._retry_tasks.clear()


class WebhookReceiver:
    """Main webhook receiver with validation, deduplication, and async processing."""
    
    def __init__(self, config: WebhookConfig):
        """
        Initialize webhook receiver.
        
        Args:
            config: Webhook configuration
        """
        self.config = config
        self.validator = SignatureValidator(
            config.secret_key,
            config.signature_algorithm,
            config.signature_format
        )
        self.dedup_cache = DeduplicationCache(config.deduplication_window)
        self.processor = EventProcessor(config, self.validator)
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
        if len(payload) > self.config.max_payload_size:
            logger.warning(f"Payload too large: {len(payload)} bytes")
            return {
                "status": "error",
                "message": f"Payload too large (max: {self.config.max_payload_size} bytes)"
            }
        
        if not self.validator.validate(payload, signature):
            logger.warning("Invalid webhook signature")
            return {
                "status": "error",
                "message": "Invalid signature"
            }
        
        try:
            payload_dict = json.loads(payload.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"Invalid payload: {e}")
            return {
                "status": "error",
                "message": "Invalid payload format"
            }
        
        if not event_id:
            event_id = payload_dict.get("id") or str(uuid.uuid4())
        
        if await self.dedup_cache.is_duplicate(event_id):
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
            timestamp=datetime.now(timezone.utc),
            signature=signature,
            raw_payload=payload
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
        
        try:
            logger.info("Waiting for queue to drain...")
            await asyncio.wait_for(
                self.event_queue.join(),
                timeout=self.config.shutdown_timeout
            )
        except asyncio.TimeoutError:
            logger.warning(
                f"Shutdown timeout reached, {self.event_queue.qsize()} events remain"
            )
        
        await self.processor.cancel_all_retries()
        
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
                logger.error(f"Worker {worker_id} error: {e}", exc_info=True)
                try:
                    self.event_queue.task_done()
                except ValueError:
                    pass
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for all queued events to be processed.
        
        Args:
            timeout: Optional timeout in seconds
            
        Returns:
            True if completed within timeout, False otherwise
        """
        try:
            if timeout:
                await asyncio.wait_for(self.event_queue.join(), timeout=timeout)
            else:
                await self.event_queue.join()
            return True
        except asyncio.TimeoutError:
            logger.warning(f"wait_for_completion timed out after {timeout}s")
            return False
    
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
        secret_key="your-secret-key-here-minimum-16-chars",
        signature_header="X-Webhook-Signature",
        max_retries=3,
        retry_delay=5,
        worker_count=3,
        handler_timeout=30
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
    signature = receiver.validator._compute_signature(payload)
    
    result = await receiver.receive_webhook(
        payload=payload,
        signature=signature,
        event_type="order.created"
    )
    
    logger.info(f"Webhook result: {result}")
    
    await receiver.wait_for_completion(timeout=10.0)
    await receiver.stop_workers()


if __name__ == "__main__":
    asyncio.run(example_usage())