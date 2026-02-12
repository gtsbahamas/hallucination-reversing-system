"""
Cursor-based pagination system for REST APIs with sorting, filtering, and consistency.
"""

import base64
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Generic, TypeVar
from urllib.parse import urlencode


class SortOrder(Enum):
    """Sort order enumeration."""
    ASC = "asc"
    DESC = "desc"


@dataclass
class SortField:
    """Represents a field to sort by."""
    field: str
    order: SortOrder = SortOrder.ASC


@dataclass
class FilterCondition:
    """Represents a filter condition."""
    field: str
    operator: str
    value: Any


@dataclass
class CursorData:
    """Internal cursor data structure."""
    sort_values: Dict[str, Any]
    primary_key: Any
    timestamp: Optional[str] = None


class Cursor:
    """Handles cursor encoding and decoding."""
    
    @staticmethod
    def encode(data: CursorData) -> str:
        """
        Encode cursor data to base64 string.
        
        Args:
            data: Cursor data to encode
            
        Returns:
            Base64 encoded cursor string
        """
        cursor_dict = asdict(data)
        json_str = json.dumps(cursor_dict, default=str, sort_keys=True)
        encoded = base64.urlsafe_b64encode(json_str.encode()).decode()
        return encoded
    
    @staticmethod
    def decode(cursor_str: str) -> CursorData:
        """
        Decode cursor string to cursor data.
        
        Args:
            cursor_str: Base64 encoded cursor string
            
        Returns:
            Decoded cursor data
            
        Raises:
            ValueError: If cursor is invalid
        """
        try:
            decoded = base64.urlsafe_b64decode(cursor_str.encode()).decode()
            cursor_dict = json.loads(decoded)
            return CursorData(**cursor_dict)
        except Exception as e:
            raise ValueError(f"Invalid cursor: {e}")


T = TypeVar('T')


@dataclass
class PaginatedResponse(Generic[T]):
    """Paginated API response."""
    data: List[T]
    next_cursor: Optional[str]
    prev_cursor: Optional[str]
    has_next: bool
    has_prev: bool
    total_count: Optional[int] = None


class CursorPaginator:
    """
    Cursor-based paginator with support for sorting, filtering, and consistency.
    """
    
    def __init__(
        self,
        primary_key: str = "id",
        default_page_size: int = 20,
        max_page_size: int = 100,
        include_total_count: bool = False
    ):
        """
        Initialize the paginator.
        
        Args:
            primary_key: Name of the primary key field
            default_page_size: Default number of items per page
            max_page_size: Maximum allowed page size
            include_total_count: Whether to include total count in response
        """
        self.primary_key = primary_key
        self.default_page_size = default_page_size
        self.max_page_size = max_page_size
        self.include_total_count = include_total_count
    
    def build_where_clause(
        self,
        filters: List[FilterCondition],
        cursor: Optional[CursorData],
        sort_fields: List[SortField],
        direction: str = "forward"
    ) -> Tuple[str, List[Any]]:
        """
        Build SQL WHERE clause for pagination with filters and cursor.
        
        Args:
            filters: List of filter conditions
            cursor: Current cursor position
            sort_fields: Fields to sort by
            direction: Pagination direction ('forward' or 'backward')
            
        Returns:
            Tuple of (WHERE clause SQL, parameters list)
        """
        conditions = []
        params = []
        
        # Apply filters
        for f in filters:
            if f.operator == "=":
                conditions.append(f"{f.field} = %s")
                params.append(f.value)
            elif f.operator == "!=":
                conditions.append(f"{f.field} != %s")
                params.append(f.value)
            elif f.operator == ">":
                conditions.append(f"{f.field} > %s")
                params.append(f.value)
            elif f.operator == ">=":
                conditions.append(f"{f.field} >= %s")
                params.append(f.value)
            elif f.operator == "<":
                conditions.append(f"{f.field} < %s")
                params.append(f.value)
            elif f.operator == "<=":
                conditions.append(f"{f.field} <= %s")
                params.append(f.value)
            elif f.operator == "IN":
                placeholders = ",".join(["%s"] * len(f.value))
                conditions.append(f"{f.field} IN ({placeholders})")
                params.extend(f.value)
            elif f.operator == "LIKE":
                conditions.append(f"{f.field} LIKE %s")
                params.append(f.value)
            elif f.operator == "IS NULL":
                conditions.append(f"{f.field} IS NULL")
            elif f.operator == "IS NOT NULL":
                conditions.append(f"{f.field} IS NOT NULL")
        
        # Apply cursor-based pagination
        if cursor:
            cursor_conditions = self._build_cursor_condition(
                cursor, sort_fields, direction
            )
            if cursor_conditions:
                conditions.append(f"({cursor_conditions[0]})")
                params.extend(cursor_conditions[1])
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        return where_clause, params
    
    def _build_cursor_condition(
        self,
        cursor: CursorData,
        sort_fields: List[SortField],
        direction: str
    ) -> Tuple[str, List[Any]]:
        """
        Build cursor comparison condition for keyset pagination.
        
        Args:
            cursor: Current cursor data
            sort_fields: Fields to sort by
            direction: Pagination direction
            
        Returns:
            Tuple of (condition SQL, parameters)
        """
        conditions = []
        params = []
        
        for i, sort_field in enumerate(sort_fields):
            field_name = sort_field.field
            field_value = cursor.sort_values.get(field_name)
            
            if field_value is None:
                continue
            
            # Determine comparison operator based on sort order and direction
            if direction == "forward":
                op = ">" if sort_field.order == SortOrder.ASC else "<"
            else:
                op = "<" if sort_field.order == SortOrder.ASC else ">"
            
            # Build condition for this level of sorting
            equals_conditions = []
            for j in range(i):
                prev_field = sort_fields[j].field
                prev_value = cursor.sort_values.get(prev_field)
                if prev_value is not None:
                    equals_conditions.append(f"{prev_field} = %s")
                    params.append(prev_value)
            
            current_condition = f"{field_name} {op} %s"
            params.append(field_value)
            
            if equals_conditions:
                condition = f"({' AND '.join(equals_conditions)} AND {current_condition})"
            else:
                condition = current_condition
            
            conditions.append(condition)
        
        # Add tie-breaker with primary key
        pk_value = cursor.primary_key
        equals_conditions = []
        for sort_field in sort_fields:
            field_value = cursor.sort_values.get(sort_field.field)
            if field_value is not None:
                equals_conditions.append(f"{sort_field.field} = %s")
                params.append(field_value)
        
        pk_op = ">" if direction == "forward" else "<"
        pk_condition = f"{self.primary_key} {pk_op} %s"
        params.append(pk_value)
        
        if equals_conditions:
            conditions.append(f"({' AND '.join(equals_conditions)} AND {pk_condition})")
        else:
            conditions.append(pk_condition)
        
        final_condition = " OR ".join(conditions) if conditions else ""
        return final_condition, params
    
    def build_order_by_clause(
        self,
        sort_fields: List[SortField],
        reverse: bool = False
    ) -> str:
        """
        Build SQL ORDER BY clause.
        
        Args:
            sort_fields: Fields to sort by
            reverse: Whether to reverse the sort order
            
        Returns:
            ORDER BY clause SQL
        """
        order_parts = []
        
        for sort_field in sort_fields:
            order = sort_field.order
            if reverse:
                order = SortOrder.DESC if order == SortOrder.ASC else SortOrder.ASC
            order_parts.append(f"{sort_field.field} {order.value.upper()}")
        
        # Always add primary key as tie-breaker
        pk_order = "DESC" if reverse else "ASC"
        order_parts.append(f"{self.primary_key} {pk_order}")
        
        return "ORDER BY " + ", ".join(order_parts)
    
    def build_query(
        self,
        base_query: str,
        filters: List[FilterCondition],
        sort_fields: List[SortField],
        cursor: Optional[str],
        page_size: int,
        direction: str = "forward"
    ) -> Tuple[str, List[Any]]:
        """
        Build complete paginated query.
        
        Args:
            base_query: Base SELECT query
            filters: List of filter conditions
            sort_fields: Fields to sort by
            cursor: Cursor string
            page_size: Number of items to fetch
            direction: Pagination direction
            
        Returns:
            Tuple of (complete query SQL, parameters)
        """
        page_size = min(page_size or self.default_page_size, self.max_page_size)
        
        cursor_data = None
        if cursor:
            cursor_data = Cursor.decode(cursor)
        
        reverse = direction == "backward"
        
        where_clause, params = self.build_where_clause(
            filters, cursor_data, sort_fields, direction
        )
        order_by_clause = self.build_order_by_clause(sort_fields, reverse)
        
        query = f"""
        {base_query}
        WHERE {where_clause}
        {order_by_clause}
        LIMIT %s
        """
        
        params.append(page_size + 1)  # Fetch one extra to check if there's more
        
        return query.strip(), params
    
    def create_cursor_from_row(
        self,
        row: Dict[str, Any],
        sort_fields: List[SortField]
    ) -> str:
        """
        Create cursor string from a data row.
        
        Args:
            row: Data row dictionary
            sort_fields: Fields used for sorting
            
        Returns:
            Encoded cursor string
        """
        sort_values = {}
        for sort_field in sort_fields:
            field_value = row.get(sort_field.field)
            sort_values[sort_field.field] = field_value
        
        cursor_data = CursorData(
            sort_values=sort_values,
            primary_key=row.get(self.primary_key),
            timestamp=datetime.utcnow().isoformat()
        )
        
        return Cursor.encode(cursor_data)
    
    def paginate(
        self,
        data: List[Dict[str, Any]],
        sort_fields: List[SortField],
        page_size: int,
        direction: str = "forward"
    ) -> PaginatedResponse:
        """
        Create paginated response from query results.
        
        Args:
            data: Query results (should include one extra row)
            sort_fields: Fields used for sorting
            page_size: Requested page size
            direction: Pagination direction
            
        Returns:
            Paginated response object
        """
        page_size = min(page_size or self.default_page_size, self.max_page_size)
        
        has_more = len(data) > page_size
        results = data[:page_size]
        
        if direction == "backward":
            results = list(reversed(results))
        
        next_cursor = None
        prev_cursor = None
        
        if has_more and direction == "forward":
            next_cursor = self.create_cursor_from_row(results[-1], sort_fields)
        
        if results and direction == "forward":
            prev_cursor = self.create_cursor_from_row(results[0], sort_fields)
        elif has_more and direction == "backward":
            prev_cursor = self.create_cursor_from_row(results[0], sort_fields)
        
        if results and direction == "backward":
            next_cursor = self.create_cursor_from_row(results[-1], sort_fields)
        
        return PaginatedResponse(
            data=results,
            next_cursor=next_cursor,
            prev_cursor=prev_cursor,
            has_next=has_more if direction == "forward" else bool(results),
            has_prev=bool(results) if direction == "forward" else has_more
        )
    
    def get_total_count_query(
        self,
        base_query: str,
        filters: List[FilterCondition]
    ) -> Tuple[str, List[Any]]:
        """
        Build query to get total count.
        
        Args:
            base_query: Base SELECT query
            filters: List of filter conditions
            
        Returns:
            Tuple of (count query SQL, parameters)
        """
        where_clause, params = self.build_where_clause(
            filters, None, [], "forward"
        )
        
        # Extract FROM clause from base query
        from_part = base_query.split("FROM", 1)[1].strip()
        
        query = f"""
        SELECT COUNT(*) as total
        FROM {from_part}
        WHERE {where_clause}
        """
        
        return query.strip(), params


class PaginationParams:
    """Helper class to parse pagination parameters from request."""
    
    @staticmethod
    def from_request(
        cursor: Optional[str] = None,
        page_size: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Parse pagination parameters from API request.
        
        Args:
            cursor: Cursor string
            page_size: Number of items per page
            sort_by: Comma-separated list of fields to sort by
            sort_order: Comma-separated list of sort orders
            filters: Dictionary of filter conditions
            
        Returns:
            Parsed parameters dictionary
        """
        sort_fields = []
        
        if sort_by:
            fields = sort_by.split(",")
            orders = (sort_order or "").split(",")
            
            for i, field in enumerate(fields):
                field = field.strip()
                order_str = orders[i].strip() if i < len(orders) else "asc"
                order = SortOrder.DESC if order_str.lower() == "desc" else SortOrder.ASC
                sort_fields.append(SortField(field=field, order=order))