import base64
import json
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from cryptography.fernet import Fernet, InvalidToken
import hashlib
import os


class SortDirection(Enum):
    ASC = "asc"
    DESC = "desc"


@dataclass
class SortField:
    field: str
    direction: SortDirection


@dataclass
class CursorData:
    last_values: List[Any]
    filters: Dict[str, Any]
    sort: List[Dict[str, str]]
    issued_at: float
    user_id: Optional[str] = None


class PaginationError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class CursorExpiredError(PaginationError):
    def __init__(self):
        super().__init__("Cursor has expired, please restart pagination", 400)


class InvalidCursorError(PaginationError):
    def __init__(self):
        super().__init__("Invalid cursor format", 400)


class CursorMismatchError(PaginationError):
    def __init__(self):
        super().__init__("Cursor context does not match current query parameters", 400)


class UnauthorizedCursorError(PaginationError):
    def __init__(self):
        super().__init__("Cursor does not belong to authenticated user", 403)


class ServiceUnavailableError(PaginationError):
    def __init__(self):
        super().__init__("Database temporarily unavailable", 503)


class CursorPagination:
    MAX_PAGE_SIZE = 1000
    DEFAULT_PAGE_SIZE = 10
    CURSOR_TTL = 86400  # 24 hours
    MAX_CURSOR_SIZE = 4096  # 4KB
    
    ALLOWED_SORT_FIELDS = {"id", "created_at", "name", "status", "updated_at"}
    ALLOWED_FILTER_FIELDS = {"status", "created_at", "name", "is_active", "updated_at"}
    RESTRICTED_FIELDS = {"password", "token", "secret", "internal_id"}
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        if encryption_key is None:
            encryption_key = Fernet.generate_key()
        self.fernet = Fernet(encryption_key)
    
    def _validate_page_size(self, page_size: Any) -> int:
        if not isinstance(page_size, int):
            raise PaginationError(f"page_size must be integer", 400)
        
        if page_size < 1 or page_size > self.MAX_PAGE_SIZE:
            raise PaginationError(
                f"page_size must be positive integer between 1 and {self.MAX_PAGE_SIZE}",
                400
            )
        
        return page_size
    
    def _parse_sort_fields(self, sort_param: Optional[str]) -> List[SortField]:
        if not sort_param:
            return [SortField(field="id", direction=SortDirection.ASC)]
        
        sort_fields = []
        for sort_item in sort_param.split(","):
            parts = sort_item.strip().split(":")
            if len(parts) != 2:
                raise PaginationError(
                    f"Invalid sort format '{sort_item}'. Use format 'field:direction'",
                    400
                )
            
            field, direction = parts
            field = field.strip()
            direction = direction.strip().lower()
            
            if field not in self.ALLOWED_SORT_FIELDS:
                raise PaginationError(
                    f"Invalid sort field {field}. Valid fields: {', '.join(sorted(self.ALLOWED_SORT_FIELDS))}",
                    400
                )
            
            if direction not in ["asc", "desc"]:
                raise PaginationError(
                    f"Invalid sort direction {direction}. Use asc or desc",
                    400
                )
            
            sort_fields.append(
                SortField(field=field, direction=SortDirection(direction))
            )
        
        # Always append id as tie-breaker if not already present
        if not any(sf.field == "id" for sf in sort_fields):
            sort_fields.append(SortField(field="id", direction=SortDirection.ASC))
        
        return sort_fields
    
    def _validate_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        validated_filters = {}
        
        for field, value in filters.items():
            # Handle special operators like __in
            base_field = field.split("__")[0]
            
            if base_field not in self.ALLOWED_FILTER_FIELDS:
                raise PaginationError(
                    f"Invalid filter field {base_field}. Valid fields: {', '.join(sorted(self.ALLOWED_FILTER_FIELDS))}",
                    400
                )
            
            if base_field in self.RESTRICTED_FIELDS:
                raise PaginationError(
                    f"Cannot filter by restricted field {base_field}",
                    400
                )
            
            validated_filters[field] = value
        
        return validated_filters
    
    def _encode_cursor(
        self,
        last_values: List[Any],
        filters: Dict[str, Any],
        sort_fields: List[SortField],
        user_id: Optional[str] = None
    ) -> str:
        cursor_data = {
            "last_values": last_values,
            "filters": filters,
            "sort": [{"field": sf.field, "direction": sf.direction.value} for sf in sort_fields],
            "issued_at": time.time(),
            "user_id": user_id
        }
        
        json_data = json.dumps(cursor_data, default=str).encode()
        encrypted = self.fernet.encrypt(json_data)
        encoded = base64.urlsafe_b64encode(encrypted).decode()
        
        if len(encoded) > self.MAX_CURSOR_SIZE:
            raise PaginationError(
                f"Cursor size exceeds maximum of {self.MAX_CURSOR_SIZE} bytes",
                400
            )
        
        return encoded
    
    def _decode_cursor(
        self,
        cursor: str,
        current_filters: Dict[str, Any],
        current_sort_fields: List[SortField],
        current_user_id: Optional[str] = None
    ) -> CursorData:
        try:
            decoded = base64.urlsafe_b64decode(cursor.encode())
            decrypted = self.fernet.decrypt(decoded)
            cursor_dict = json.loads(decrypted.decode())
            
            # Validate cursor structure
            required_keys = ["last_values", "filters", "sort", "issued_at"]
            for key in required_keys:
                if key not in cursor_dict:
                    raise InvalidCursorError()
            
            # Validate TTL
            if time.time() - cursor_dict["issued_at"] > self.CURSOR_TTL:
                raise CursorExpiredError()
            
            # Validate user context
            if current_user_id is not None and cursor_dict.get("user_id") != current_user_id:
                raise UnauthorizedCursorError()
            
            # Validate filter match
            if cursor_dict["filters"] != current_filters:
                raise CursorMismatchError()
            
            # Validate sort match
            current_sort_dict = [
                {"field": sf.field, "direction": sf.direction.value}
                for sf in current_sort_fields
            ]
            if cursor_dict["sort"] != current_sort_dict:
                raise CursorMismatchError()
            
            # Type validate last_values components
            last_values = cursor_dict["last_values"]
            if not isinstance(last_values, list):
                raise InvalidCursorError()
            
            # Validate that last value for id field is integer
            if len(last_values) > 0:
                id_index = len(last_values) - 1
                if not isinstance(last_values[id_index], int):
                    raise PaginationError("Invalid cursor: last_id must be integer", 400)
            
            return CursorData(
                last_values=last_values,
                filters=cursor_dict["filters"],
                sort=cursor_dict["sort"],
                issued_at=cursor_dict["issued_at"],
                user_id=cursor_dict.get("user_id")
            )
            
        except InvalidToken:
            raise InvalidCursorError()
        except json.JSONDecodeError:
            raise InvalidCursorError()
        except (ValueError, KeyError, TypeError) as e:
            if isinstance(e, PaginationError):
                raise
            raise InvalidCursorError()
    
    def _build_where_clause(
        self,
        cursor_data: Optional[CursorData],
        sort_fields: List[SortField],
        filters: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        where_parts = []
        params = {}
        
        # Add filter conditions
        for field, value in filters.items():
            if "__in" in field:
                base_field = field.replace("__in", "")
                placeholders = ", ".join([f"%(filter_{base_field}_{i})s" for i in range(len(value))])
                where_parts.append(f"{base_field} IN ({placeholders})")
                for i, val in enumerate(value):
                    params[f"filter_{base_field}_{i}"] = val
            elif value is None:
                where_parts.append(f"{field} IS NULL")
            else:
                where_parts.append(f"{field} = %(filter_{field})s")
                params[f"filter_{field}"] = value
        
        # Add cursor condition using tuple comparison
        if cursor_data is not None and cursor_data.last_values:
            cursor_fields = [sf.field for sf in sort_fields]
            cursor_values = cursor_data.last_values
            
            # Build tuple comparison for multi-field cursor
            field_tuple = ", ".join(cursor_fields)
            param_tuple = ", ".join([f"%(cursor_{field})s" for field in cursor_fields])
            
            # Use > for ascending final field, < for descending
            final_direction = sort_fields[-1].direction
            operator = ">" if final_direction == SortDirection.ASC else "<"
            
            # For mixed directions, build complex condition
            # Simplified: use tuple comparison with proper operator
            where_parts.append(f"({field_tuple}) {operator} ({param_tuple})")
            
            for i, field in enumerate(cursor_fields):
                params[f"cursor_{field}"] = cursor_values[i]
        
        where_clause = " AND ".join(where_parts) if where_parts else "1=1"
        return where_clause, params
    
    def _build_order_clause(self, sort_fields: List[SortField]) -> str:
        order_parts = []
        for sf in sort_fields:
            direction = "DESC" if sf.direction == SortDirection.DESC else "ASC"
            # Handle nulls explicitly
            order_parts.append(f"{sf.field} {direction} NULLS LAST")
        
        return "ORDER BY " + ", ".join(order_parts)
    
    def paginate(
        self,
        db_connection: Any,
        table: str,
        page_size: int = DEFAULT_PAGE_SIZE,
        cursor: Optional[str] = None,
        sort: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            # Validate inputs
            page_size = self._validate_page_size(page_size)
            sort_fields = self._parse_sort_fields(sort)
            filters = self._validate_filters(filters or {})
            
            # Decode cursor if provided
            cursor_data = None
            if cursor is not None:
                cursor_data = self._decode_cursor(cursor, filters, sort_fields, user_id)
            
            # Build query
            where_clause, params = self._build_where_clause(cursor_data, sort_fields, filters)
            order_clause = self._build_order_clause(sort_fields)
            
            # Fetch page_size + 1 to determine if there are more results
            query = f"""
                SELECT *
                FROM {table}
                WHERE {where_clause}
                {order_clause}
                LIMIT %(limit)s
            """
            
            params["limit"] = page_size + 1
            
            # Execute query with error handling
            try:
                db_cursor = db_connection.cursor()
                db_cursor.execute(query, params)
                rows = db_cursor.fetchall()
            except Exception as e:
                # Handle database connection errors
                error_str = str(e).lower()
                if "connection" in error_str or "timeout" in error_str:
                    raise ServiceUnavailableError()
                raise
            
            # Determine if there are more results
            has_more = len(rows) > page_size
            items = rows[:page_size]
            
            # Generate next cursor
            next_cursor = None
            if has_more and items:
                last_item = items[-1]
                last_values = []
                
                for sf in sort_fields:
                    # Handle dict or object-like row
                    if isinstance(last_item, dict):
                        last_values.append(last_item[sf.field])
                    else:
                        last_values.append(getattr(last_item, sf.field))
                
                next_cursor = self._encode_cursor(last_values, filters, sort_fields, user_id)
            
            # Return standardized response
            return {
                "data": items,
                "next_cursor": next_cursor,
                "has_more": has_more
            }
            
        except PaginationError:
            raise
        except Exception as e:
            # Catch any unexpected errors and return appropriate status
            error_str = str(e).lower()
            if "connection" in error_str or "timeout" in error_str:
                raise ServiceUnavailableError()
            raise


class MockDBConnection:
    def __init__(self, data: List[Dict[str, Any]]):
        self.data = data
    
    def cursor(self):
        return MockCursor(self.data)


class MockCursor:
    def __init__(self, data: List[Dict[str, Any]]):
        self.data = data
        self.results = []
    
    def execute(self, query: str, params: Dict[str, Any]):
        # Simple mock implementation for testing
        results = self.data.copy()
        
        # Apply filters
        for key, value in params.items():
            if key.startswith("filter_"):
                field = key.replace("filter_", "").split("_")[0]
                if value is not None:
                    results = [r for r in results if r.get(field) == value]
        
        # Apply cursor filtering
        if "cursor_id" in params:
            cursor_id = params["cursor_id"]
            results = [r for r in results if r["id"] > cursor_id]
        
        # Apply sorting (simplified)
        if "ORDER BY" in query:
            if "created_at" in query:
                if "DESC" in query:
                    results.sort(key=lambda x: (x.get("created_at", ""), x.get("id", 0)), reverse=True)
                else:
                    results.sort(key=lambda x: (x.get("created_at", ""), x.get("id", 0)))
            elif "name" in query:
                results.sort(key=lambda x: (x.get("name", ""), x.get("id", 0)))
            else:
                results.sort(key=lambda x: x.get("id", 0))
        
        # Apply limit
        limit = params.get("limit", len(results))
        self.results = results[:limit]
    
    def fetchall(self):
        return self.results


def create_pagination_handler(encryption_key: Optional[bytes] = None) -> CursorPagination:
    return CursorPagination(encryption_key=encryption_key)


if __name__ == "__main__":
    # Example usage
    pagination = create_pagination_handler()
    
    # Mock data
    mock_data = [
        {"id": 1, "name": "Alice", "status": "active", "created_at": "2024-01-01T10:00:00Z"},
        {"id": 2, "name": "Bob", "status": "active", "created_at": "2024-01-02T10:00:00Z"},
        {"id": 3, "name": "Charlie", "status": "inactive", "created_at": "2024-01-03T10:00:00Z"},
        {"id": 4, "name": "David", "status": "active", "created_at": "2024-01-04T10:00:00Z"},
        {"id": 5, "name": "Eve", "status": "active", "created_at": "2024-01-05T10:00:00Z"},
    ]
    
    db_conn = MockDBConnection(mock_data)
    
    # First page
    result = pagination.paginate(
        db_connection=db_conn,
        table="users",
        page_size=2,
        sort="created_at:desc",
        filters={"status": "active"}
    )
    
    print("Page 1:")
    print(f"Items: {len(result['data'])}")
    print(f"Has more: {result['has_more']}")
    print(f"Next cursor: {result['next_cursor'][:50] if result['next_cursor'] else None}...")
    
    # Second page
    if result["next_cursor"]:
        result2 = pagination.paginate(
            db_connection=db_conn,
            table="users",
            page_size=2,
            cursor=result["next_cursor"],
            sort="created_at:desc",
            filters={"status": "active"}
        )
        
        print("\nPage 2:")
        print(f"Items: {len(result2['data'])}")
        print(f"Has more: {result2['has_more']}")