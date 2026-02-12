"""
Cursor-based pagination system for REST APIs with sorting, filtering, and consistency.
"""

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Generic, TypeVar, Set, Union
import secrets


class SortOrder(Enum):
    """Sort order enumeration."""
    ASC = "asc"
    DESC = "desc"


@dataclass
class SortField:
    """Represents a field to sort by."""
    field: str
    order: SortOrder = SortOrder.ASC
    nulls_last: bool = True


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
    timestamp: str
    version: int = 1


class Cursor:
    """Handles cursor encoding and decoding with integrity verification."""
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize cursor handler.
        
        Args:
            secret_key: Secret key for HMAC signature. If None, generates random key.
        """
        self.secret_key = secret_key or secrets.token_hex(32)
    
    def encode(self, data: CursorData) -> str:
        """
        Encode cursor data to base64 string with HMAC signature.
        
        Args:
            data: Cursor data to encode
            
        Returns:
            Base64 encoded cursor string with signature
        """
        cursor_dict = asdict(data)
        json_str = json.dumps(cursor_dict, default=str, sort_keys=True)
        
        signature = hmac.new(
            self.secret_key.encode(),
            json_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        signed_data = f"{json_str}|{signature}"
        encoded = base64.urlsafe_b64encode(signed_data.encode()).decode()
        return encoded
    
    def decode(self, cursor_str: str) -> CursorData:
        """
        Decode cursor string to cursor data with signature verification.
        
        Args:
            cursor_str: Base64 encoded cursor string
            
        Returns:
            Decoded cursor data
            
        Raises:
            ValueError: If cursor is invalid or signature verification fails
        """
        if not cursor_str:
            raise ValueError("Empty cursor string")
        
        try:
            decoded = base64.urlsafe_b64decode(cursor_str.encode()).decode()
            parts = decoded.split('|')
            
            if len(parts) != 2:
                raise ValueError("Invalid cursor format")
            
            json_str, signature = parts
            
            expected_signature = hmac.new(
                self.secret_key.encode(),
                json_str.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                raise ValueError("Cursor signature verification failed")
            
            cursor_dict = json.loads(json_str)
            return CursorData(**cursor_dict)
        except (ValueError, KeyError, json.JSONDecodeError, TypeError) as e:
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
    
    ALLOWED_OPERATORS = {'=', '!=', '>', '>=', '<', '<=', 'IN', 'LIKE', 'IS NULL', 'IS NOT NULL'}
    MAX_SORT_FIELDS = 10
    MAX_FILTERS = 50
    CURSOR_TTL_SECONDS = 3600
    
    def __init__(
        self,
        primary_key: str = "id",
        default_page_size: int = 20,
        max_page_size: int = 100,
        include_total_count: bool = False,
        allowed_fields: Optional[Set[str]] = None,
        secret_key: Optional[str] = None,
        param_style: str = "%s",
        snapshot_timestamp_field: Optional[str] = None
    ):
        """
        Initialize the paginator.
        
        Args:
            primary_key: Name of the primary key field
            default_page_size: Default number of items per page
            max_page_size: Maximum allowed page size
            include_total_count: Whether to include total count in response
            allowed_fields: Set of allowed field names for security
            secret_key: Secret key for cursor signatures
            param_style: SQL parameter placeholder style ('%s' or '?')
            snapshot_timestamp_field: Field name for snapshot isolation (e.g., 'created_at')
        """
        if default_page_size < 1 or max_page_size < 1:
            raise ValueError("Page sizes must be positive")
        
        self.primary_key = primary_key
        self.default_page_size = default_page_size
        self.max_page_size = max_page_size
        self.include_total_count = include_total_count
        self.allowed_fields = allowed_fields or set()
        self.cursor_handler = Cursor(secret_key)
        self.param_style = param_style
        self.snapshot_timestamp_field = snapshot_timestamp_field
        
        if primary_key not in self.allowed_fields and self.allowed_fields:
            self.allowed_fields.add(primary_key)
    
    def _validate_field(self, field_name: str) -> None:
        """
        Validate field name against allowlist.
        
        Args:
            field_name: Field name to validate
            
        Raises:
            ValueError: If field is not allowed
        """
        if self.allowed_fields and field_name not in self.allowed_fields:
            raise ValueError(f"Field '{field_name}' is not allowed")
        
        if not field_name or not field_name.replace('_', '').isalnum():
            raise ValueError(f"Invalid field name: '{field_name}'")
    
    def _validate_operator(self, operator: str) -> None:
        """
        Validate filter operator.
        
        Args:
            operator: Operator to validate
            
        Raises:
            ValueError: If operator is not allowed
        """
        if operator not in self.ALLOWED_OPERATORS:
            raise ValueError(f"Operator '{operator}' is not allowed")
    
    def _validate_cursor_expiry(self, cursor: CursorData) -> None:
        """
        Validate cursor has not expired.
        
        Args:
            cursor: Cursor data to validate
            
        Raises:
            ValueError: If cursor has expired
        """
        try:
            cursor_time = datetime.fromisoformat(cursor.timestamp)
            age = datetime.utcnow() - cursor_time
            if age.total_seconds() > self.CURSOR_TTL_SECONDS:
                raise ValueError("Cursor has expired")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid cursor timestamp: {e}")
    
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
            
        Raises:
            ValueError: If validation fails
        """
        if len(filters) > self.MAX_FILTERS:
            raise ValueError(f"Too many filters (max {self.MAX_FILTERS})")
        
        conditions = []
        params = []
        
        for f in filters:
            self._validate_field(f.field)
            self._validate_operator(f.operator)
            
            if f.operator == "=":
                conditions.append(f"{f.field} = {self.param_style}")
                params.append(f.value)
            elif f.operator == "!=":
                conditions.append(f"{f.field} != {self.param_style}")
                params.append(f.value)
            elif f.operator == ">":
                conditions.append(f"{f.field} > {self.param_style}")
                params.append(f.value)
            elif f.operator == ">=":
                conditions.append(f"{f.field} >= {self.param_style}")
                params.append(f.value)
            elif f.operator == "<":
                conditions.append(f"{f.field} < {self.param_style}")
                params.append(f.value)
            elif f.operator == "<=":
                conditions.append(f"{f.field} <= {self.param_style}")
                params.append(f.value)
            elif f.operator == "IN":
                if not f.value or not isinstance(f.value, (list, tuple)):
                    continue
                if len(f.value) == 0:
                    continue
                placeholders = ",".join([self.param_style] * len(f.value))
                conditions.append(f"{f.field} IN ({placeholders})")
                params.extend(f.value)
            elif f.operator == "LIKE":
                conditions.append(f"{f.field} LIKE {self.param_style}")
                params.append(f.value)
            elif f.operator == "IS NULL":
                conditions.append(f"{f.field} IS NULL")
            elif f.operator == "IS NOT NULL":
                conditions.append(f"{f.field} IS NOT NULL")
        
        if cursor:
            self._validate_cursor_expiry(cursor)
            
            if self.snapshot_timestamp_field:
                conditions.append(f"{self.snapshot_timestamp_field} <= {self.param_style}")
                params.append(cursor.timestamp)
            
            cursor_conditions = self._build_cursor_condition(
                cursor, sort_fields, direction
            )
            if cursor_conditions[0]:
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
        if not sort_fields:
            return "", []
        
        conditions = []
        params = []
        
        for i, sort_field in enumerate(sort_fields):
            field_name = sort_field.field
            field_value = cursor.sort_values.get(field_name)
            
            if direction == "forward":
                op = ">" if sort_field.order == SortOrder.ASC else "<"
                null_op = "IS NOT NULL"
            else:
                op = "<" if sort_field.order == SortOrder.ASC else ">"
                null_op = "IS NULL"
            
            equals_conditions = []
            for j in range(i):
                prev_field = sort_fields[j].field
                prev_value = cursor.sort_values.get(prev_field)
                
                if prev_value is None:
                    equals_conditions.append(f"{prev_field} IS NULL")
                else:
                    equals_conditions.append(f"{prev_field} = {self.param_style}")
                    params.append(prev_value)
            
            if field_value is None:
                current_condition = f"{field_name} {null_op}"
            else:
                current_condition = f"{field_name} {op} {self.param_style}"
                params.append(field_value)
            
            if equals_conditions:
                condition = f"({' AND '.join(equals_conditions)} AND {current_condition})"
            else:
                condition = current_condition
            
            conditions.append(condition)
        
        pk_value = cursor.primary_key
        equals_conditions = []
        for sort_field in sort_fields:
            field_value = cursor.sort_values.get(sort_field.field)
            if field_value is None:
                equals_conditions.append(f"{sort_field.field} IS NULL")
            else:
                equals_conditions.append(f"{sort_field.field} = {self.param_style}")
                params.append(field_value)
        
        pk_op = ">" if direction == "forward" else "<"
        pk_condition = f"{self.primary_key} {pk_op} {self.param_style}"
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
            
        Raises:
            ValueError: If validation fails
        """
        if len(sort_fields) > self.MAX_SORT_FIELDS:
            raise ValueError(f"Too many sort fields (max {self.MAX_SORT_FIELDS})")
        
        order_parts = []
        
        for sort_field in sort_fields:
            self._validate_field(sort_field.field)
            
            order = sort_field.order
            if reverse:
                order = SortOrder.DESC if order == SortOrder.ASC else SortOrder.ASC
            
            nulls_clause = "NULLS LAST" if sort_field.nulls_last else "NULLS FIRST"
            if reverse:
                nulls_clause = "NULLS FIRST" if sort_field.nulls_last else "NULLS LAST"
            
            order_parts.append(f"{sort_field.field} {order.value.upper()} {nulls_clause}")
        
        pk_order = "DESC" if reverse else "ASC"
        order_parts.append(f"{self.primary_key} {pk_order}")
        
        return "ORDER BY " + ", ".join(order_parts)
    
    def build_query(
        self,
        table_name: str,
        columns: List[str],
        filters: List[FilterCondition],
        sort_fields: List[SortField],
        cursor: Optional[str],
        page_size: Optional[int],
        direction: str = "forward"
    ) -> Tuple[str, List[Any]]:
        """
        Build complete paginated query.
        
        Args:
            table_name: Name of the table to query
            columns: List of column names to select
            filters: List of filter conditions
            sort_fields: Fields to sort by
            cursor: Cursor string
            page_size: Number of items to fetch
            direction: Pagination direction
            
        Returns:
            Tuple of (complete query SQL, parameters)
            
        Raises:
            ValueError: If validation fails
        """
        if not table_name or not table_name.replace('_', '').isalnum():
            raise ValueError(f"Invalid table name: '{table_name}'")
        
        if not columns:
            raise ValueError("Column list cannot be empty")
        
        for col in columns:
            self._validate_field(col)
        
        if not sort_fields:
            raise ValueError("At least one sort field is required")
        
        if page_size is not None and page_size < 1:
            raise ValueError("page_size must be positive")
        
        page_size = min(page_size or self.default_page_size, self.max_page_size)
        
        cursor_data = None
        if cursor:
            try:
                cursor_data = self.cursor_handler.decode(cursor)
            except ValueError as e:
                raise ValueError(f"Invalid cursor: {e}")
        
        reverse = direction == "backward"
        
        where_clause, params = self.build_where_clause(
            filters, cursor_data, sort_fields, direction
        )
        order_by_clause = self.build_order_by_clause(sort_fields, reverse)
        
        column_list = ", ".join(columns)
        
        query = f"""
        SELECT {column_list}
        FROM {table_name}
        WHERE {where_clause}
        {order_by_clause}
        LIMIT {self.param_style}
        """
        
        params.append(page_size + 1)
        
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
            timestamp=datetime.utcnow().isoformat(),
            version=1
        )
        
        return self.cursor_handler.encode(cursor_data)
    
    def paginate(
        self,
        data: List[Dict[str, Any]],
        sort_fields: List[SortField],
        page_size: Optional[int],
        direction: str = "forward",
        total_count: Optional[int] = None
    ) -> PaginatedResponse:
        """
        Create paginated response from query results.
        
        Args:
            data: Query results (should include one extra row)
            sort_fields: Fields used for sorting
            page_size: Requested page size
            direction: Pagination direction
            total_count: Optional total count of all results
            
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
        has_next = False
        has_prev = False
        
        if direction == "forward":
            has_next = has_more
            has_prev = bool(results)
            
            if has_more and results:
                next_cursor = self.create_cursor_from_row(results[-1], sort_fields)
            if results:
                prev_cursor = self.create_cursor_from_row(results[0], sort_fields)
        else:
            has_next = bool(results)
            has_prev = has_more
            
            if results:
                next_cursor = self.create_cursor_from_row(results[-1], sort_fields)
            if has_more and results:
                prev_cursor = self.create_cursor_from_row(results[0], sort_fields)
        
        return PaginatedResponse(
            data=results,
            next_cursor=next_cursor,
            prev_cursor=prev_cursor,
            has_next=has_next,
            has_prev=has_prev,
            total_count=total_count if self.include_total_count else None
        )
    
    def get_total_count_query(
        self,
        table_name: str,
        filters: List[FilterCondition],
        has_joins: bool = False
    ) -> Tuple[str, List[Any]]:
        """
        Build query to get total count.
        
        Args:
            table_name: Name of the table
            filters: List of filter conditions
            has_joins: Whether the query involves JOINs (requires DISTINCT)
            
        Returns:
            Tuple of (count query SQL, parameters)
        """
        if not table_name or not table_name.replace('_', '').isalnum():
            raise ValueError(f"Invalid table name: '{table_name}'")
        
        where_clause, params = self.build_where_clause(
            filters, None, [], "forward"
        )
        
        count_expr = f"COUNT(DISTINCT {self.primary_key})" if has_joins else "COUNT(*)"
        
        query = f"""
        SELECT {count_expr} as total
        FROM {table_name}
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
        filters: Optional[Dict[str, Any]] = None,
        filter_operators: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Parse pagination parameters from API request.
        
        Args:
            cursor: Cursor string
            page_size: Number of items per page
            sort_by: Comma-separated list of fields to sort by
            sort_order: Comma-separated list of sort orders
            filters: Dictionary of filter conditions {field: value}
            filter_operators: Dictionary mapping field to operator {field: operator}
            
        Returns:
            Parsed parameters dictionary with keys:
                - cursor: str
                - page_size: int
                - sort_fields: List[SortField]
                - filters: List[FilterCondition]
        """
        sort_fields = []
        
        if sort_by:
            fields = [f.strip() for f in sort_by.split(",") if f.strip()]
            orders = [o.strip() for o in (sort_order or "").split(",")]
            
            for i, field in enumerate(fields):
                order_str = orders[i] if i < len(orders) else "asc"
                order = SortOrder.DESC if order_str.lower() == "desc" else SortOrder.ASC
                sort_fields.append(SortField(field=field, order=order))
        
        filter_conditions = []
        if filters:
            operators = filter_operators or {}
            for field, value in filters.items():
                operator = operators.get(field, "=")
                if value is not None:
                    filter_conditions.append(
                        FilterCondition(field=field, operator=operator, value=value)
                    )
        
        return {
            "cursor": cursor,
            "page_size": page_size,
            "sort_fields": sort_fields,
            "filters": filter_conditions
        }