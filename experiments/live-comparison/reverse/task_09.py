import json
import uuid
import re
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field, asdict
from threading import Lock
from collections import defaultdict
import copy


class ConcurrencyException(Exception):
    """Raised when optimistic locking detects a version conflict."""
    
    def __init__(self, aggregate_id: str, expected_version: int, actual_version: int):
        self.aggregate_id = aggregate_id
        self.expected_version = expected_version
        self.actual_version = actual_version
        super().__init__(
            f'Conflict on {aggregate_id}: expected version {expected_version}, actual version {actual_version}'
        )


class DataTooLargeException(Exception):
    """Raised when event data exceeds size limit."""
    pass


@dataclass(frozen=True)
class Event:
    """Immutable event record."""
    event_id: str
    aggregate_id: str
    event_type: str
    data: Dict[str, Any]
    version: int
    timestamp: datetime


@dataclass(frozen=True)
class Snapshot:
    """Immutable snapshot record."""
    aggregate_id: str
    version: int
    state: Dict[str, Any]
    timestamp: datetime


class EventStore:
    """Event store with optimistic locking and snapshot support."""
    
    def __init__(self):
        self._events: Dict[str, List[Event]] = defaultdict(list)
        self._snapshots: Dict[str, List[Snapshot]] = {}
        self._aggregate_locks: Dict[str, Lock] = defaultdict(Lock)
        self._version_counters: Dict[str, int] = defaultdict(int)
        self._max_data_size = 1_000_000  # 1MB limit
    
    def _validate_aggregate_id(self, aggregate_id: Any) -> None:
        """Validate aggregate_id is non-empty string."""
        if not isinstance(aggregate_id, str):
            raise TypeError('aggregate_id must be string')
        if not aggregate_id:
            raise ValueError('aggregate_id must be non-empty string')
    
    def _validate_event_type(self, event_type: Any) -> None:
        """Validate event_type is non-empty string."""
        if not isinstance(event_type, str):
            raise TypeError('event_type must be string')
        if not event_type:
            raise ValueError('event_type must be non-empty string')
    
    def _validate_data(self, data: Any) -> Dict[str, Any]:
        """Validate and normalize event data."""
        if data is None:
            return {}
        if not isinstance(data, dict):
            raise TypeError('data must be dict')
        
        # Deep copy to ensure immutability
        validated_data = copy.deepcopy(data)
        
        # Check JSON serializability
        try:
            serialized = json.dumps(validated_data)
        except TypeError as e:
            raise ValueError('data must be JSON-serializable') from e
        
        # Check size limit
        if len(serialized) > self._max_data_size:
            raise DataTooLargeException('data exceeds size limit')
        
        return validated_data
    
    def _validate_expected_version(self, expected_version: Any) -> None:
        """Validate expected_version type."""
        if expected_version is not None and not isinstance(expected_version, int):
            raise TypeError('expected_version must be int or None')
    
    def _validate_from_version(self, from_version: Any) -> None:
        """Validate from_version parameter."""
        if from_version is not None:
            if not isinstance(from_version, int):
                raise TypeError('from_version must be int')
            if from_version < 0:
                raise ValueError('from_version must be non-negative')
    
    def _validate_snapshot_version(self, version: Any) -> None:
        """Validate snapshot version."""
        if not isinstance(version, int):
            raise TypeError('version must be int')
        if version < 0:
            raise ValueError('version must be non-negative')
    
    def _get_current_version(self, aggregate_id: str) -> int:
        """Get current version for aggregate."""
        return self._version_counters[aggregate_id]
    
    def _get_next_version(self, aggregate_id: str) -> int:
        """Atomically increment and return next version for aggregate."""
        self._version_counters[aggregate_id] += 1
        return self._version_counters[aggregate_id]
    
    def append_event(
        self,
        aggregate_id: str,
        event_type: str,
        data: Dict[str, Any],
        expected_version: Optional[int] = None
    ) -> Event:
        """
        Append event to aggregate with optimistic locking.
        
        Args:
            aggregate_id: Unique identifier for the aggregate
            event_type: Type/name of the event
            data: Event payload as dictionary
            expected_version: Expected current version for optimistic locking
            
        Returns:
            The created Event object
            
        Raises:
            ValueError: If aggregate_id, event_type, or data is invalid
            TypeError: If parameters have wrong types
            ConcurrencyException: If expected_version doesn't match current version
            DataTooLargeException: If data exceeds size limit
        """
        # Validate inputs
        self._validate_aggregate_id(aggregate_id)
        self._validate_event_type(event_type)
        validated_data = self._validate_data(data)
        self._validate_expected_version(expected_version)
        
        # Acquire per-aggregate lock
        with self._aggregate_locks[aggregate_id]:
            # Get current version
            current_version = self._get_current_version(aggregate_id)
            
            # Optimistic locking check
            if expected_version is not None:
                if expected_version != current_version:
                    raise ConcurrencyException(
                        aggregate_id,
                        expected_version,
                        current_version
                    )
            
            # Generate event metadata
            event_id = str(uuid.uuid4())
            timestamp = datetime.utcnow()
            next_version = self._get_next_version(aggregate_id)
            
            # Create immutable event
            event = Event(
                event_id=event_id,
                aggregate_id=aggregate_id,
                event_type=event_type,
                data=validated_data,
                version=next_version,
                timestamp=timestamp
            )
            
            # Store event
            self._events[aggregate_id].append(event)
            
            return event
    
    def get_events(
        self,
        aggregate_id: str,
        from_version: Optional[int] = None
    ) -> List[Event]:
        """
        Retrieve events for aggregate.
        
        Args:
            aggregate_id: Unique identifier for the aggregate
            from_version: Optional minimum version (inclusive)
            
        Returns:
            List of events in version order
            
        Raises:
            ValueError: If from_version is negative
            TypeError: If from_version is not int
        """
        self._validate_aggregate_id(aggregate_id)
        self._validate_from_version(from_version)
        
        # Get events for aggregate
        events = self._events.get(aggregate_id, [])
        
        # Filter by version if specified
        if from_version is not None:
            events = [e for e in events if e.version >= from_version]
        
        # Sort by version to ensure order
        return sorted(events, key=lambda e: e.version)
    
    def save_snapshot(
        self,
        aggregate_id: str,
        version: int,
        state: Dict[str, Any]
    ) -> None:
        """
        Save snapshot of aggregate state at specific version.
        
        Args:
            aggregate_id: Unique identifier for the aggregate
            version: Version number of the state
            state: Aggregate state as dictionary
            
        Raises:
            ValueError: If aggregate_id is invalid or version is negative
            TypeError: If version is not int
        """
        self._validate_aggregate_id(aggregate_id)
        self._validate_snapshot_version(version)
        
        # Deep copy state to ensure immutability
        state_copy = copy.deepcopy(state)
        
        # Create snapshot
        snapshot = Snapshot(
            aggregate_id=aggregate_id,
            version=version,
            state=state_copy,
            timestamp=datetime.utcnow()
        )
        
        # Store snapshot
        if aggregate_id not in self._snapshots:
            self._snapshots[aggregate_id] = []
        self._snapshots[aggregate_id].append(snapshot)
    
    def get_snapshot(self, aggregate_id: str) -> Optional[Snapshot]:
        """
        Retrieve most recent snapshot for aggregate.
        
        Args:
            aggregate_id: Unique identifier for the aggregate
            
        Returns:
            Most recent Snapshot or None if no snapshots exist
        """
        self._validate_aggregate_id(aggregate_id)
        
        snapshots = self._snapshots.get(aggregate_id)
        if not snapshots:
            return None
        
        # Return snapshot with highest version
        return max(snapshots, key=lambda s: s.version)
    
    def rebuild_aggregate(
        self,
        aggregate_id: str,
        apply_event: Callable[[Dict[str, Any], Event], Dict[str, Any]],
        initial_state: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Rebuild aggregate state by replaying events.
        
        Args:
            aggregate_id: Unique identifier for the aggregate
            apply_event: Function that applies event to state
            initial_state: Starting state (defaults to empty dict)
            
        Returns:
            Final aggregate state after applying all events
            
        Raises:
            ValueError: If aggregate_id is invalid
            TypeError: If apply_event is not callable
        """
        self._validate_aggregate_id(aggregate_id)
        
        if not callable(apply_event):
            raise TypeError('apply_event must be callable')
        
        if initial_state is None:
            initial_state = {}
        
        # Start with initial state
        state = copy.deepcopy(initial_state)
        
        # Check for snapshot
        snapshot = self.get_snapshot(aggregate_id)
        if snapshot:
            # Load snapshot state
            state = copy.deepcopy(snapshot.state)
            # Get events after snapshot
            events = self.get_events(aggregate_id, from_version=snapshot.version + 1)
        else:
            # Get all events
            events = self.get_events(aggregate_id)
        
        # Apply events in order
        for event in events:
            state = apply_event(state, event)
        
        return state