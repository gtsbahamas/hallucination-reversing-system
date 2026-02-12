import asyncio
import base64
import hashlib
import hmac
import json
import logging
import os
import random
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from functools import lru_cache
from typing import Any, Callable, Dict, Optional, Set
from uuid import uuid4
import sqlite3
from contextlib import contextmanager
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when required configuration is missing."""
    pass


class WebhookError(Exception):
    """Base exception for webhook processing errors."""
    pass


class SignatureValidationError(WebhookError):
    """Raised when signature validation fails."""
    pass


class EventStatus(Enum):
    """Event processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    DLQ = "dlq"


@dataclass
class WebhookEvent:
    """Represents a webhook event."""
    id: str
    type: str
    payload: Dict[str, Any]
    timestamp: Optional[str] = None
    entity_id: Optional[str] = None


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = 5
    base_delay: float = 1.0
    max_delay: float = 300.0
    jitter: bool = True


@dataclass
class DeduplicationConfig:
    """Configuration for event deduplication."""
    ttl: int = 86400  # 24 hours default
    storage_backend: str = "sqlite"


class DeduplicationStore:
    """Handles event deduplication with persistence."""
    
    def __init__(self, db_path: str = "webhooks.db", ttl: int = 86400):
        self.db_path = db_path
        self.ttl = ttl
        self.lock = threading.Lock()
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize the database schema."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS processed_events (
                    event_id VARCHAR(1000) PRIMARY KEY,
                    processed_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_event_id 
                ON processed_events(event_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at 
                ON processed_events(created_at)
            """)
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        try:
            yield conn
        finally:
            conn.close()
    
    def is_duplicate(self, event_id: str) -> bool:
        """Check if event has been processed (O(1) indexed lookup)."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM processed_events WHERE event_id = ? LIMIT 1",
                (event_id,)
            )
            return cursor.fetchone() is not None
    
    def mark_processed(self, event_id: str) -> bool:
        """
        Atomically mark event as processed.
        Returns True if successful, False if duplicate.
        """
        with self.lock:
            try:
                with self._get_connection() as conn:
                    conn.execute(
                        """INSERT INTO processed_events (event_id, processed_at) 
                           VALUES (?, ?)""",
                        (event_id, datetime.utcnow().isoformat())
                    )
                    conn.commit()
                    return True
            except sqlite3.IntegrityError:
                # Duplicate event_id (primary key constraint)
                return False
    
    def cleanup_expired(self) -> int:
        """Remove expired deduplication entries. Returns number of deleted entries."""
        expiry_time = datetime.utcnow() - timedelta(seconds=self.ttl)
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM processed_events WHERE created_at < ?",
                (expiry_time.isoformat(),)
            )
            conn.commit()
            return cursor.rowcount


class DeadLetterQueue:
    """Stores failed events after max retries."""
    
    def __init__(self, db_path: str = "webhooks.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize DLQ table."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dead_letter_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id VARCHAR(1000) NOT NULL,
                    payload TEXT NOT NULL,
                    error_type TEXT,
                    error_message TEXT,
                    attempts INTEGER NOT NULL,
                    failed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        try:
            yield conn
        finally:
            conn.close()
    
    def store(
        self,
        event_id: str,
        payload: Dict[str, Any],
        error: str,
        attempts: int
    ) -> None:
        """Store a failed event in the DLQ."""
        error_type = error.split(':')[0] if ':' in error else 'UnknownError'
        with self._get_connection() as conn:
            conn.execute(
                """INSERT INTO dead_letter_queue 
                   (event_id, payload, error_type, error_message, attempts)
                   VALUES (?, ?, ?, ?, ?)""",
                (event_id, json.dumps(payload), error_type, error, attempts)
            )
            conn.commit()
        logger.error(
            f'Event moved to DLQ',
            extra={
                'event_id': event_id,
                'attempts': attempts,
                'error': error
            }
        )
    
    def get_all(self) -> list:
        """Retrieve all events from DLQ."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT event_id, payload, error_type, error_message, attempts, failed_at FROM dead_letter_queue"
            )
            return cursor.fetchall()


class AsyncTaskQueue:
    """Manages asynchronous event processing with retry logic."""
    
    def __init__(
        self,
        max_concurrent_tasks: int = 10,
        retry_config: Optional[RetryConfig] = None
    ):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.retry_config = retry_config or RetryConfig()
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.tasks: Set[asyncio.Task] = set()
        self.dlq = DeadLetterQueue()
    
    def enqueue(
        self,
        event: WebhookEvent,
        processor: Callable[[WebhookEvent], None]
    ) -> None:
        """Enqueue an event for async processing."""
        task = asyncio.create_task(self._process_with_retry(event, processor))
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
    
    async def _process_with_retry(
        self,
        event: WebhookEvent,
        processor: Callable[[WebhookEvent], None]
    ) -> None:
        """Process event with exponential backoff retry logic."""
        async with self.semaphore:
            for attempt in range(self.retry_config.max_retries):
                try:
                    await asyncio.to_thread(processor, event)
                    logger.info(
                        'Event processed successfully',
                        extra={
                            'event_id': event.id,
                            'type': event.type,
                            'attempt': attempt + 1
                        }
                    )
                    return
                except Exception as e:
                    error_msg = f"{type(e).__name__}: {str(e)}"
                    logger.error(
                        'Event processing failed',
                        extra={
                            'event_id': event.id,
                            'attempt': attempt + 1,
                            'error': type(e).__name__,
                            'error_msg': str(e)
                        }
                    )
                    
                    if attempt >= self.retry_config.max_retries - 1:
                        # Max retries exceeded, move to DLQ
                        self.dlq.store(
                            event_id=event.id,
                            payload=event.payload,
                            error=error_msg,
                            attempts=attempt + 1
                        )
                        return
                    
                    # Calculate backoff delay with exponential backoff and jitter
                    delay = min(
                        self.retry_config.base_delay * (2 ** attempt),
                        self.retry_config.max_delay
                    )
                    if self.retry_config.jitter:
                        delay += random.uniform(0, 1)
                    
                    await asyncio.sleep(delay)


class SignatureValidator:
    """Validates HMAC signatures with constant-time comparison."""
    
    ALGORITHM_MAP = {
        'sha256': hashlib.sha256,
        'sha1': hashlib.sha1,
        'sha512': hashlib.sha512
    }
    
    def __init__(self, secrets: Optional[Dict[str, str]] = None):
        """
        Initialize validator with webhook secrets.
        
        Args:
            secrets: Dict mapping sender_id to secret key
        """
        if secrets is None:
            # Load default secret from environment
            default_secret = os.environ.get('WEBHOOK_SECRET')
            if not default_secret:
                raise ConfigurationError('WEBHOOK_SECRET not set')
            secrets = {'default': default_secret}
        self.secrets = secrets
    
    @lru_cache(maxsize=128)
    def _get_hmac_func(self, algorithm: str):
        """Cache HMAC hash functions for performance."""
        return self.ALGORITHM_MAP.get(algorithm, hashlib.sha256)
    
    def validate_signature(
        self,
        payload: bytes,
        signature: Optional[str],
        secret: str,
        algorithm: str = 'sha256'
    ) -> bool:
        """
        Validate HMAC signature using constant-time comparison.
        
        Args:
            payload: Raw request body bytes
            signature: Signature from request header
            secret: Webhook secret key
            algorithm: Hash algorithm (sha256, sha1, sha512)
        
        Returns:
            True if signature is valid, False otherwise
        """
        # Type validation
        if not signature or not isinstance(signature, str):
            return False
        
        if not secret or not isinstance(secret, str):
            return False
        
        # Parse signature (handle different formats)
        parsed_sig = self._parse_signature(signature)
        
        # Compute expected signature
        hash_func = self._get_hmac_func(algorithm)
        expected_hmac = hmac.new(
            secret.encode('utf-8'),
            payload,
            hash_func
        )
        expected_sig = expected_hmac.hexdigest()
        
        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_sig, parsed_sig)
    
    def _parse_signature(self, signature: str) -> str:
        """Parse signature supporting multiple formats."""
        # Remove common prefixes
        sig = signature.strip()
        for prefix in ['sha256=', 'sha1=', 'sha512=']:
            if sig.lower().startswith(prefix):
                sig = sig[len(prefix):]
                break
        
        # Try to decode base64 if it looks like base64
        if '=' in sig and len(sig) % 4 == 0:
            try:
                decoded = base64.b64decode(sig)
                sig = decoded.hex()
            except Exception:
                pass  # Not base64, use as-is
        
        return sig.lower()
    
    def get_secret(self, sender_id: str = 'default') -> str:
        """Get secret for a specific sender."""
        secret = self.secrets.get(sender_id)
        if not secret:
            raise ConfigurationError(f'No secret configured for sender: {sender_id}')
        return secret


class WebhookReceiver:
    """
    Main webhook receiver handling validation, deduplication, and async processing.
    """
    
    MAX_BODY_SIZE = 1024 * 1024  # 1MB
    
    def __init__(
        self,
        secrets: Optional[Dict[str, str]] = None,
        retry_config: Optional[RetryConfig] = None,
        dedup_config: Optional[DeduplicationConfig] = None,
        max_concurrent_tasks: int = 10
    ):
        """
        Initialize webhook receiver.
        
        Args:
            secrets: Webhook secrets per sender
            retry_config: Retry configuration
            dedup_config: Deduplication configuration
            max_concurrent_tasks: Max concurrent processing tasks
        """
        self.validator = SignatureValidator(secrets)
        self.dedup_config = dedup_config or DeduplicationConfig()
        self.dedup_store = DeduplicationStore(
            ttl=self.dedup_config.ttl
        )
        self.task_queue = AsyncTaskQueue(
            max_concurrent_tasks=max_concurrent_tasks,
            retry_config=retry_config or RetryConfig()
        )
        self.event_processor: Optional[Callable[[WebhookEvent], None]] = None
        
        # Start cleanup task
        asyncio.create_task(self._periodic_cleanup())
    
    async def _periodic_cleanup(self) -> None:
        """Periodically clean up expired deduplication entries."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                deleted = self.dedup_store.cleanup_expired()
                if deleted > 0:
                    logger.info(f'Cleaned up {deleted} expired deduplication entries')
            except Exception as e:
                logger.error(f'Cleanup task error: {e}')
    
    def set_event_processor(self, processor: Callable[[WebhookEvent], None]) -> None:
        """Set the event processor callback."""
        self.event_processor = processor
    
    def handle_webhook(
        self,
        request_body: Optional[bytes],
        signature_header: Optional[str],
        sender_id: str = 'default',
        algorithm: str = 'sha256'
    ) -> tuple[Dict[str, Any], int]:
        """
        Handle incoming webhook request.
        
        Args:
            request_body: Raw request body bytes
            signature_header: Signature from request header
            sender_id: Identifier for webhook sender
            algorithm: HMAC algorithm to use
        
        Returns:
            Tuple of (response_dict, status_code)
        """
        # Validate body size
        if request_body and len(request_body) > self.MAX_BODY_SIZE:
            return {
                'error': 'payload_too_large'
            }, 413
        
        # Check for empty body
        if not request_body:
            return {
                'error': 'empty_body'
            }, 400
        
        # Check for missing signature
        if not signature_header:
            return {
                'error': 'missing_signature'
            }, 401
        
        # Validate signature BEFORE parsing JSON
        secret = self.validator.get_secret(sender_id)
        if not self.validator.validate_signature(
            request_body,
            signature_header,
            secret,
            algorithm
        ):
            return {
                'error': 'invalid_signature'
            }, 401
        
        # Parse JSON
        try:
            payload = json.loads(request_body.decode('utf-8'))
        except json.JSONDecodeError:
            return {
                'error': 'invalid_json'
            }, 400
        
        # Process event asynchronously
        try:
            result = self.process_event(payload)
            if result.get('duplicate_detected'):
                logger.info(
                    'Duplicate event detected',
                    extra={'event_id': result.get('event_id')}
                )
        except Exception as e:
            # Log error but still return 200 (async processing error)
            logger.error(f'Error enqueuing event: {e}')
        
        # Always return 200 for valid webhooks
        return {'status': 'accepted'}, 200
    
    def process_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process webhook event with deduplication.
        
        Args:
            payload: Event payload dict
        
        Returns:
            Dict with processing result
        """
        # Handle missing event ID
        if 'id' not in payload:
            # Generate deterministic ID from content hash
            normalized = json.dumps(payload, sort_keys=True).encode('utf-8')
            event_id = hashlib.sha256(normalized).hexdigest()
            payload['id'] = event_id
            logger.warning(
                'Event missing ID, generated deterministic ID',
                extra={'event_id': event_id}
            )
        else:
            event_id = payload['id']
        
        # Check for duplicate
        if self.dedup_store.is_duplicate(event_id):
            return {
                'event_id': event_id,
                'duplicate_detected': True,
                'status': 'skipped'
            }
        
        # Atomically mark as processed
        if not self.dedup_store.mark_processed(event_id):
            # Race condition - another thread marked it first
            return {
                'event_id': event_id,
                'duplicate_detected': True,
                'status': 'skipped'
            }
        
        # Check for future timestamp (warning only)
        if payload.get('timestamp'):
            try:
                event_time = datetime.fromisoformat(
                    payload['timestamp'].replace('Z', '+00:00')
                )
                if event_time > datetime.utcnow():
                    logger.warning(
                        'Future timestamp detected',
                        extra={
                            'event_id': event_id,
                            'timestamp': payload['timestamp']
                        }
                    )
            except Exception:
                pass  # Invalid timestamp format, continue processing
        
        # Create event object
        event = WebhookEvent(
            id=event_id,
            type=payload.get('type', 'unknown'),
            payload=payload,
            timestamp=payload.get('timestamp'),
            entity_id=payload.get('entity_id') or payload.get('entity')
        )
        
        # Enqueue for async processing
        if self.event_processor:
            self.task_queue.enqueue(event, self.event_processor)
        
        return {
            'event_id': event_id,
            'duplicate_detected': False,
            'status': 'processing'
        }


# Example usage and event processor
def example_event_processor(event: WebhookEvent) -> None:
    """
    Example event processor that can be customized.
    This would contain your business logic.
    """
    logger.info(
        'Processing event',
        extra={
            'event_id': event.id,
            'type': event.type
        }
    )
    
    # Simulate processing time
    time.sleep(0.1)
    
    # Your business logic here
    if event.type == 'payment.completed':
        # Handle payment completion
        pass
    elif event.type == 'user.created':
        # Handle user creation
        pass
    
    # Simulate occasional failures for testing
    if random.random() < 0.1:
        raise Exception("Random processing error for testing")


# Initialize receiver with configuration
def create_webhook_receiver() -> WebhookReceiver:
    """Factory function to create configured webhook receiver."""
    # Load secrets from environment
    webhook_secret = os.environ.get('WEBHOOK_SECRET')
    if not webhook_secret:
        raise ConfigurationError('WEBHOOK_SECRET environment variable not set')
    
    secrets = {
        'default': webhook_secret,
        'prod': os.environ.get('WEBHOOK_SECRET_PROD', webhook_secret),
        'test': os.environ.get('WEBHOOK_SECRET_TEST', webhook_secret)
    }
    
    # Configure retry behavior
    retry_config = RetryConfig(
        max_retries=int(os.environ.get('WEBHOOK_MAX_RETRIES', '5')),
        base_delay=float(os.environ.get('WEBHOOK_BASE_DELAY', '1.0')),
        max_delay=float(os.environ.get('WEBHOOK_MAX_DELAY', '300.0'))
    )
    
    # Configure deduplication
    dedup_config = DeduplicationConfig(
        ttl=int(os.environ.get('WEBHOOK_DEDUP_TTL', '86400'))
    )
    
    # Create receiver
    receiver = WebhookReceiver(
        secrets=secrets,
        retry_config=retry_config,
        dedup_config=dedup_config,
        max_concurrent_tasks=int(os.environ.get('WEBHOOK_MAX_CONCURRENT', '10'))
    )
    
    # Set event processor
    receiver.set_event_processor(example_event_processor)
    
    return receiver


# Example Flask integration
def flask_webhook_endpoint():
    """Example Flask endpoint for webhook handling."""
    try:
        from flask import Flask, request, jsonify
        
        app = Flask(__name__)
        
        # Set a default secret for example purposes
        if not os.environ.get('WEBHOOK_SECRET'):
            os.environ['WEBHOOK_SECRET'] = 'example_secret_key_change_in_production'
        
        receiver = create_webhook_receiver()
        
        @app.route('/webhook', methods=['POST'])
        def webhook():
            """Webhook endpoint."""
            signature = request.headers.get('X-Signature') or request.headers.get('X-Hub-Signature-256')
            sender_id = request.headers.get('X-Sender-ID', 'default')
            
            response, status_code = receiver.handle_webhook(
                request_body=request.get_data(),
                signature_header=signature,
                sender_id=sender_id
            )
            
            return jsonify(response), status_code
        
        return app
    except ImportError:
        logger.warning("Flask not installed, skipping Flask integration example")
        return None


if __name__ == '__main__':
    # Example standalone usage
    import sys
    
    # Set example environment variable
    os.environ['WEBHOOK_SECRET'] = 'test_secret_key_12345'
    
    # Create receiver
    receiver = create_webhook_receiver()
    
    # Example webhook simulation
    example_payload = json.dumps({
        'id': 'evt_' + str(uuid4()),
        'type': 'payment.completed',
        'amount': 100,
        'currency': 'USD',
        'user': {
            'id': 'user_123',
            'email': 'user@example.com'
        },
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }).encode('utf-8')
    
    # Generate valid signature
    secret = os.environ['WEBHOOK_SECRET']
    signature = hmac.new(
        secret.encode('utf-8'),
        example_payload,
        hashlib.sha256
    ).hexdigest()
    
    # Process webhook
    response, status = receiver.handle_webhook(
        request_body=example_payload,
        signature_header=signature
    )
    
    print(f"Response: {response}, Status: {status}")
    
    # Keep async tasks running
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)