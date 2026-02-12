import json
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, Type, TypeVar
from uuid import UUID, uuid4
from collections import defaultdict
from copy import deepcopy


class Event(Protocol):
    """Protocol for events that can be stored in the event store."""
    
    event_id: UUID
    aggregate_id: UUID
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]
    version: int


@dataclass
class EventData:
    """Concrete implementation of an event."""
    
    event_id: UUID
    aggregate_id: UUID
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]
    version: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary representation."""
        return {
            'event_id': str(self.event_id),
            'aggregate_id': str(self.aggregate_id),
            'event_type': self.event_type,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'version': self.version,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EventData':
        """Create event from dictionary representation."""
        return cls(
            event_id=UUID(data['event_id']),
            aggregate_id=UUID(data['aggregate_id']),
            event_type=data['event_type'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            data=data['data'],
            version=data['version'],
            metadata=data.get('metadata', {})
        )


@dataclass
class Snapshot:
    """Represents a point-in-time snapshot of aggregate state."""
    
    snapshot_id: UUID
    aggregate_id: UUID
    version: int
    state: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary representation."""
        return {
            'snapshot_id': str(self.snapshot_id),
            'aggregate_id': str(self.aggregate_id),
            'version': self.version,
            'state': self.state,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Snapshot':
        """Create snapshot from dictionary representation."""
        return cls(
            snapshot_id=UUID(data['snapshot_id']),
            aggregate_id=UUID(data['aggregate_id']),
            version=data['version'],
            state=data['state'],
            timestamp=datetime.fromisoformat(data['timestamp'])
        )


class ConcurrencyError(Exception):
    """Raised when optimistic locking detects a concurrent modification."""
    
    def __init__(self, aggregate_id: UUID, expected_version: int, actual_version: int):
        self.aggregate_id = aggregate_id
        self.expected_version = expected_version
        self.actual_version = actual_version
        super().__init__(
            f"Concurrency conflict for aggregate {aggregate_id}: "
            f"expected version {expected_version}, but actual version is {actual_version}"
        )


class AggregateNotFoundError(Exception):
    """Raised when an aggregate is not found in the event store."""
    
    def __init__(self, aggregate_id: UUID):
        self.aggregate_id = aggregate_id
        super().__init__(f"Aggregate {aggregate_id} not found")


class InvalidEventError(Exception):
    """Raised when an event is invalid."""
    pass


class VersionContinuityError(Exception):
    """Raised when event version continuity is broken."""
    pass


TAggregate = TypeVar('TAggregate')


class Aggregate(Protocol):
    """Protocol for aggregates that can be reconstituted from events."""
    
    aggregate_id: UUID
    version: int
    
    def apply_event(self, event: EventData) -> None:
        """Apply an event to modify the aggregate's state."""
        ...
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert aggregate state to dictionary."""
        ...
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Aggregate':
        """Reconstitute aggregate from dictionary state."""
        ...


class EventStore:
    """
    Event store implementation with support for:
    - Appending events
    - Rebuilding aggregate state
    - Snapshots for performance optimization
    - Optimistic locking for concurrent writes
    """
    
    def __init__(self, snapshot_frequency: int = 10):
        """
        Initialize the event store.
        
        Args:
            snapshot_frequency: Number of events between automatic snapshots
        """
        self._events: Dict[UUID, List[EventData]] = {}
        self._snapshots: Dict[UUID, Snapshot] = {}
        self._versions: Dict[UUID, int] = {}
        self._locks: Dict[UUID, threading.RLock] = {}
        self._global_lock = threading.RLock()
        self._snapshot_frequency = max(1, snapshot_frequency)
        self._aggregate_types: Dict[UUID, Type[Aggregate]] = {}
    
    def _get_lock(self, aggregate_id: UUID) -> threading.RLock:
        """
        Get or create a lock for an aggregate in a thread-safe manner.
        
        Args:
            aggregate_id: ID of the aggregate
            
        Returns:
            RLock for the aggregate
        """
        if aggregate_id in self._locks:
            return self._locks[aggregate_id]
        
        with self._global_lock:
            if aggregate_id not in self._locks:
                self._locks[aggregate_id] = threading.RLock()
            return self._locks[aggregate_id]
    
    def _validate_events(self, aggregate_id: UUID, events: List[EventData]) -> None:
        """
        Validate events before appending.
        
        Args:
            aggregate_id: Expected aggregate ID
            events: Events to validate
            
        Raises:
            InvalidEventError: If events are invalid
        """
        if not events:
            raise InvalidEventError("Cannot append empty event list")
        
        for event in events:
            if not isinstance(event, EventData):
                raise InvalidEventError(f"Event must be EventData instance, got {type(event)}")
            
            if not event.event_type:
                raise InvalidEventError("Event must have an event_type")
            
            if event.data is None:
                raise InvalidEventError("Event must have data")
            
            if event.aggregate_id != aggregate_id and event.aggregate_id != UUID(int=0):
                raise InvalidEventError(
                    f"Event aggregate_id {event.aggregate_id} does not match expected {aggregate_id}"
                )
    
    def append_events(
        self,
        aggregate_id: UUID,
        events: List[EventData],
        expected_version: int
    ) -> None:
        """
        Append events to the event stream with optimistic locking.
        
        Args:
            aggregate_id: ID of the aggregate
            events: List of events to append
            expected_version: Expected current version of the aggregate
            
        Raises:
            ConcurrencyError: If expected_version doesn't match current version
            InvalidEventError: If events are invalid
        """
        if not isinstance(aggregate_id, UUID):
            raise InvalidEventError(f"aggregate_id must be UUID, got {type(aggregate_id)}")
        
        if not isinstance(expected_version, int) or expected_version < 0:
            raise InvalidEventError(f"expected_version must be non-negative integer, got {expected_version}")
        
        self._validate_events(aggregate_id, events)
        
        lock = self._get_lock(aggregate_id)
        
        with lock:
            current_version = self._versions.get(aggregate_id, 0)
            
            if current_version != expected_version:
                raise ConcurrencyError(aggregate_id, expected_version, current_version)
            
            if aggregate_id not in self._events:
                self._events[aggregate_id] = []
            
            for i, event in enumerate(events):
                new_version = current_version + i + 1
                
                event.version = new_version
                event.aggregate_id = aggregate_id
                
                if event.event_id is None or event.event_id == UUID(int=0):
                    event.event_id = uuid4()
                
                if event.timestamp is None:
                    event.timestamp = datetime.utcnow()
                
                self._events[aggregate_id].append(event)
            
            self._versions[aggregate_id] = current_version + len(events)
            
            if self._should_create_snapshot(aggregate_id):
                self._create_snapshot_internal(aggregate_id)
    
    def get_events(
        self,
        aggregate_id: UUID,
        from_version: int = 0,
        to_version: Optional[int] = None
    ) -> List[EventData]:
        """
        Retrieve events for an aggregate within a version range.
        
        Args:
            aggregate_id: ID of the aggregate
            from_version: Starting version (exclusive)
            to_version: Ending version (inclusive), None for all events
            
        Returns:
            List of events in version order
        """
        lock = self._get_lock(aggregate_id)
        
        with lock:
            events = self._events.get(aggregate_id, [])
            
            filtered_events = [
                e for e in events
                if e.version > from_version and (to_version is None or e.version <= to_version)
            ]
            
            return sorted(filtered_events, key=lambda e: e.version)
    
    def _verify_version_continuity(self, events: List[EventData], start_version: int) -> None:
        """
        Verify that events form a continuous version sequence.
        
        Args:
            events: Events to verify
            start_version: Expected starting version
            
        Raises:
            VersionContinuityError: If versions are not continuous
        """
        expected = start_version + 1
        for event in events:
            if event.version != expected:
                raise VersionContinuityError(
                    f"Version discontinuity: expected {expected}, got {event.version}"
                )
            expected += 1
    
    def rebuild_aggregate(
        self,
        aggregate_type: Type[TAggregate],
        aggregate_id: UUID
    ) -> TAggregate:
        """
        Rebuild an aggregate from its event stream, using snapshots when available.
        
        Args:
            aggregate_type: Type of aggregate to reconstitute
            aggregate_id: ID of the aggregate
            
        Returns:
            Reconstituted aggregate instance
            
        Raises:
            AggregateNotFoundError: If no events exist for the aggregate
        """
        lock = self._get_lock(aggregate_id)
        
        with lock:
            snapshot = self._snapshots.get(aggregate_id)
            
            if snapshot:
                try:
                    aggregate = aggregate_type.from_dict(deepcopy(snapshot.state))
                    from_version = snapshot.version
                except Exception as e:
                    raise InvalidEventError(f"Failed to restore from snapshot: {e}")
            else:
                aggregate = aggregate_type(aggregate_id=aggregate_id, version=0)
                from_version = 0
            
            events = self.get_events(aggregate_id, from_version=from_version)
            
            if from_version == 0 and not events:
                raise AggregateNotFoundError(aggregate_id)
            
            if events:
                try:
                    self._verify_version_continuity(events, from_version)
                except VersionContinuityError:
                    pass
            
            for event in events:
                try:
                    aggregate.apply_event(event)
                    aggregate.version = event.version
                except Exception as e:
                    raise InvalidEventError(f"Failed to apply event {event.event_id}: {e}")
            
            with self._global_lock:
                self._aggregate_types[aggregate_id] = aggregate_type
            
            return aggregate
    
    def create_snapshot(
        self,
        aggregate_id: UUID,
        aggregate: Aggregate
    ) -> Snapshot:
        """
        Manually create a snapshot of an aggregate's current state.
        
        Args:
            aggregate_id: ID of the aggregate
            aggregate: Current aggregate instance
            
        Returns:
            Created snapshot
        """
        if aggregate.aggregate_id != aggregate_id:
            raise InvalidEventError(
                f"Aggregate ID mismatch: expected {aggregate_id}, got {aggregate.aggregate_id}"
            )
        
        lock = self._get_lock(aggregate_id)
        
        with lock:
            current_version = self._versions.get(aggregate_id, 0)
            
            if aggregate.version > current_version:
                raise InvalidEventError(
                    f"Aggregate version {aggregate.version} exceeds current version {current_version}"
                )
            
            try:
                state = deepcopy(aggregate.to_dict())
            except Exception as e:
                raise InvalidEventError(f"Failed to serialize aggregate state: {e}")
            
            snapshot = Snapshot(
                snapshot_id=uuid4(),
                aggregate_id=aggregate_id,
                version=aggregate.version,
                state=state,
                timestamp=datetime.utcnow()
            )
            
            self._snapshots[aggregate_id] = snapshot
            return snapshot
    
    def _create_snapshot_internal(self, aggregate_id: UUID) -> None:
        """
        Internal method to create snapshot automatically.
        
        Args:
            aggregate_id: ID of the aggregate
        """
        try:
            with self._global_lock:
                aggregate_type = self._aggregate_types.get(aggregate_id)
            
            if aggregate_type:
                aggregate = self.rebuild_aggregate(aggregate_type, aggregate_id)
                self.create_snapshot(aggregate_id, aggregate)
        except Exception:
            pass
    
    def _should_create_snapshot(self, aggregate_id: UUID) -> bool:
        """
        Determine if a snapshot should be created based on frequency.
        
        Args:
            aggregate_id: ID of the aggregate
            
        Returns:
            True if snapshot should be created
        """
        snapshot = self._snapshots.get(aggregate_id)
        current_version = self._versions.get(aggregate_id, 0)
        
        if not snapshot:
            return current_version >= self._snapshot_frequency
        
        return current_version - snapshot.version >= self._snapshot_frequency
    
    def get_snapshot(self, aggregate_id: UUID) -> Optional[Snapshot]:
        """
        Retrieve the latest snapshot for an aggregate.
        
        Args:
            aggregate_id: ID of the aggregate
            
        Returns:
            Latest snapshot or None if no snapshot exists
        """
        lock = self._get_lock(aggregate_id)
        
        with lock:
            snapshot = self._snapshots.get(aggregate_id)
            return deepcopy(snapshot) if snapshot else None
    
    def get_current_version(self, aggregate_id: UUID) -> int:
        """
        Get the current version of an aggregate.
        
        Args:
            aggregate_id: ID of the aggregate
            
        Returns:
            Current version number
        """
        lock = self._get_lock(aggregate_id)
        
        with lock:
            return self._versions.get(aggregate_id, 0)
    
    def get_all_events(self, aggregate_id: UUID) -> List[EventData]:
        """
        Retrieve all events for an aggregate.
        
        Args:
            aggregate_id: ID of the aggregate
            
        Returns:
            All events in version order
        """
        return self.get_events(aggregate_id, from_version=0)
    
    def exists(self, aggregate_id: UUID) -> bool:
        """
        Check if an aggregate exists in the store.
        
        Args:
            aggregate_id: ID of the aggregate
            
        Returns:
            True if aggregate has events, False otherwise
        """
        lock = self._get_lock(aggregate_id)
        
        with lock:
            return aggregate_id in self._events and len(self._events[aggregate_id]) > 0


class InMemoryEventStore(EventStore):
    """In-memory implementation of event store for testing and development."""
    
    def clear(self) -> None:
        """Clear all events and snapshots from the store."""
        with self._global_lock:
            self._events.clear()
            self._snapshots.clear()
            self._versions.clear()
            self._locks.clear()
            self._aggregate_types.clear()
    
    def export_events(self, aggregate_id: UUID) -> str:
        """
        Export events as JSON string.
        
        Args:
            aggregate_id: ID of the aggregate
            
        Returns:
            JSON string representation of events
        """
        events = self.get_all_events(aggregate_id)
        return json.dumps([e.to_dict() for e in events], indent=2)
    
    def import_events(self, aggregate_id: UUID, json_data: str) -> None:
        """
        Import events from JSON string.
        
        Args:
            aggregate_id: ID of the aggregate
            json_data: JSON string representation of events
        """
        if not json_data or not json_data.strip():
            raise InvalidEventError("Cannot import empty JSON data")
        
        try:
            events_data = json.loads(json_data)
        except json.JSONDecodeError as e:
            raise InvalidEventError(f"Invalid JSON data: {e}")
        
        if not isinstance(events_data, list):
            raise InvalidEventError("JSON data must be a list of events")
        
        events = []
        for e in events_data:
            try:
                events.append(EventData.from_dict(e))
            except Exception as ex:
                raise InvalidEventError(f"Failed to parse event: {ex}")
        
        lock = self._get_lock(aggregate_id)
        
        with lock:
            self._events[aggregate_id] = sorted(events, key=lambda e: e.version)
            
            if events:
                max_version = max(e.version for e in events)
                self._versions[aggregate_id] = max_version
                
                try:
                    self._verify_version_continuity(self._events[aggregate_id], 0)
                except VersionContinuityError:
                    pass