import os
import re
import json
import yaml
from typing import Any, Dict, List, Optional, Union, Type
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from copy import deepcopy


class ConfigType(Enum):
    """Supported configuration file types."""
    YAML = "yaml"
    JSON = "json"


class ValidationErrorType(Enum):
    """Types of validation errors."""
    MISSING_FIELD = "missing_field"
    TYPE_MISMATCH = "type_mismatch"
    INVALID_VALUE = "invalid_value"
    EXTRA_FIELD = "extra_field"
    ENV_VAR_NOT_FOUND = "env_var_not_found"


@dataclass
class ValidationError:
    """Represents a configuration validation error."""
    error_type: ValidationErrorType
    path: str
    message: str
    expected: Optional[Any] = None
    actual: Optional[Any] = None


class ConfigValidationException(Exception):
    """Exception raised when configuration validation fails."""
    
    def __init__(self, errors: List[ValidationError]):
        self.errors = errors
        super().__init__(self._format_errors())
    
    def _format_errors(self) -> str:
        """Format validation errors into a readable message."""
        lines = ["Configuration validation failed with the following errors:"]
        for i, error in enumerate(self.errors, 1):
            lines.append(f"\n{i}. Error at '{error.path}':")
            lines.append(f"   Type: {error.error_type.value}")
            lines.append(f"   Message: {error.message}")
            if error.expected is not None:
                lines.append(f"   Expected: {error.expected}")
            if error.actual is not None:
                lines.append(f"   Actual: {error.actual}")
        return "\n".join(lines)


class SchemaField:
    """Represents a field in the configuration schema."""
    
    def __init__(
        self,
        field_type: Union[Type[Any], List[Type[Any]]],
        required: bool = True,
        default: Any = None,
        allowed_values: Optional[List[Any]] = None,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        description: Optional[str] = None,
        item_schema: Optional[Union['SchemaField', Dict]] = None,
    ):
        self.field_type = field_type if isinstance(field_type, list) else [field_type]
        self.required = required
        self.default = default
        self.allowed_values = allowed_values
        self.min_value = min_value
        self.max_value = max_value
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = pattern
        self.description = description
        self.item_schema = item_schema
        
        self._validate_schema_field()
    
    def _validate_schema_field(self) -> None:
        """Validate that the schema field itself is correctly defined."""
        if not self.field_type:
            raise ValueError("field_type cannot be empty")
        
        for t in self.field_type:
            if not isinstance(t, type):
                raise ValueError(f"field_type must contain type objects, got {t}")
        
        if self.pattern is not None:
            try:
                re.compile(self.pattern)
            except re.error as e:
                raise ValueError(f"Invalid regex pattern: {e}")
        
        if self.min_value is not None and self.max_value is not None:
            if self.min_value > self.max_value:
                raise ValueError("min_value cannot be greater than max_value")
        
        if self.min_length is not None and self.min_length < 0:
            raise ValueError("min_length cannot be negative")
        
        if self.max_length is not None and self.max_length < 0:
            raise ValueError("max_length cannot be negative")
        
        if self.min_length is not None and self.max_length is not None:
            if self.min_length > self.max_length:
                raise ValueError("min_length cannot be greater than max_length")


class ConfigSchema:
    """Defines the schema for configuration validation."""
    
    def __init__(self, schema: Dict[str, Union[SchemaField, Dict]]):
        self.schema = schema
        self._validate_schema(schema, "root")
    
    def _validate_schema(self, schema: Any, path: str) -> None:
        """Validate that the schema structure is correct."""
        if not isinstance(schema, dict):
            raise ValueError(f"Schema at '{path}' must be a dictionary")
        
        for key, value in schema.items():
            field_path = f"{path}.{key}"
            if isinstance(value, SchemaField):
                pass
            elif isinstance(value, dict):
                self._validate_schema(value, field_path)
            else:
                raise ValueError(
                    f"Schema at '{field_path}' must be SchemaField or dict, got {type(value).__name__}"
                )
    
    def get_field(self, path: str) -> Optional[Union[SchemaField, Dict]]:
        """Get a field from the schema by its path."""
        parts = path.split('.')
        current = self.schema
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        return current


class ConfigLoader:
    """Loads and validates configuration from YAML or JSON files."""
    
    ENV_VAR_PATTERN = re.compile(r'\$\{([^}]+)\}')
    ENV_VAR_NAME_PATTERN = re.compile(r'^[A-Z_][A-Z0-9_]*$', re.IGNORECASE)
    
    def __init__(
        self,
        schema: Optional[ConfigSchema] = None,
        strict: bool = True,
        allow_extra_fields: bool = False,
        encoding: str = 'utf-8',
    ):
        self.schema = schema
        self.strict = strict
        self.allow_extra_fields = allow_extra_fields
        self.encoding = encoding
        self.errors: List[ValidationError] = []
    
    def load(self, config_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load configuration from a file and validate it.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Validated configuration dictionary
            
        Raises:
            ConfigValidationException: If validation fails
            FileNotFoundError: If the config file doesn't exist
            ValueError: If the file format is not supported or parsing fails
        """
        self.errors = []
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        config_type = self._detect_config_type(config_path)
        raw_config = self._load_file(config_path, config_type)
        
        if raw_config is None:
            raise ValueError(f"Configuration file is empty or contains null: {config_path}")
        
        config = self._interpolate_env_vars(raw_config)
        
        if self.errors:
            raise ConfigValidationException(self.errors)
        
        if self.schema:
            config = self._apply_defaults(config, self.schema.schema, "")
            self._validate(config, self.schema.schema, "")
            
            if self.errors:
                raise ConfigValidationException(self.errors)
        
        return config
    
    def load_from_dict(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load configuration from a dictionary and validate it.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Validated configuration dictionary
            
        Raises:
            ConfigValidationException: If validation fails
        """
        self.errors = []
        config = deepcopy(config)
        config = self._interpolate_env_vars(config)
        
        if self.errors:
            raise ConfigValidationException(self.errors)
        
        if self.schema:
            config = self._apply_defaults(config, self.schema.schema, "")
            self._validate(config, self.schema.schema, "")
            
            if self.errors:
                raise ConfigValidationException(self.errors)
        
        return config
    
    def _detect_config_type(self, config_path: Path) -> ConfigType:
        """Detect configuration file type from extension."""
        suffix = config_path.suffix.lower()
        
        if suffix in ['.yaml', '.yml']:
            return ConfigType.YAML
        elif suffix == '.json':
            return ConfigType.JSON
        else:
            raise ValueError(f"Unsupported configuration file type: {suffix}")
    
    def _load_file(self, config_path: Path, config_type: ConfigType) -> Dict[str, Any]:
        """Load configuration from file based on type."""
        try:
            with open(config_path, 'r', encoding=self.encoding) as f:
                if config_type == ConfigType.YAML:
                    result = yaml.safe_load(f)
                    return result if result is not None else {}
                else:
                    return json.load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse YAML file: {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON file at line {e.lineno}, column {e.colno}: {e.msg}")
        except UnicodeDecodeError as e:
            raise ValueError(f"Failed to decode file with encoding '{self.encoding}': {e}")
    
    def _interpolate_env_vars(self, config: Any, path: str = "") -> Any:
        """
        Recursively interpolate environment variables in configuration.
        
        Supports ${VAR_NAME} and ${VAR_NAME:default_value} syntax.
        """
        if isinstance(config, dict):
            return {
                key: self._interpolate_env_vars(value, f"{path}.{key}" if path else key)
                for key, value in config.items()
            }
        elif isinstance(config, list):
            return [
                self._interpolate_env_vars(item, f"{path}[{i}]")
                for i, item in enumerate(config)
            ]
        elif isinstance(config, str):
            return self._substitute_env_vars(config, path)
        else:
            return config
    
    def _substitute_env_vars(self, value: str, path: str) -> str:
        """Substitute environment variables in a string."""
        def replace_env_var(match: re.Match) -> str:
            var_expr = match.group(1)
            
            if ':' in var_expr:
                parts = var_expr.split(':', 1)
                var_name = parts[0].strip()
                default = parts[1].strip()
                
                if not self.ENV_VAR_NAME_PATTERN.match(var_name):
                    self.errors.append(ValidationError(
                        error_type=ValidationErrorType.ENV_VAR_NOT_FOUND,
                        path=path,
                        message=f"Invalid environment variable name: '{var_name}'",
                    ))
                    return match.group(0)
                
                if var_name in os.environ:
                    return os.environ[var_name]
                else:
                    return default
            else:
                var_name = var_expr.strip()
                
                if not self.ENV_VAR_NAME_PATTERN.match(var_name):
                    self.errors.append(ValidationError(
                        error_type=ValidationErrorType.ENV_VAR_NOT_FOUND,
                        path=path,
                        message=f"Invalid environment variable name: '{var_name}'",
                    ))
                    return match.group(0)
                
                if var_name in os.environ:
                    return os.environ[var_name]
                elif self.strict:
                    self.errors.append(ValidationError(
                        error_type=ValidationErrorType.ENV_VAR_NOT_FOUND,
                        path=path,
                        message=f"Environment variable '{var_name}' not found and no default provided",
                    ))
                    return match.group(0)
                else:
                    return match.group(0)
        
        return self.ENV_VAR_PATTERN.sub(replace_env_var, value)
    
    def _apply_defaults(
        self,
        config: Any,
        schema: Dict[str, Union[SchemaField, Dict]],
        path: str,
    ) -> Any:
        """Apply default values to configuration."""
        if not isinstance(config, dict):
            return config
        
        result = dict(config)
        
        for key, field_schema in schema.items():
            field_path = f"{path}.{key}" if path else key
            
            if isinstance(field_schema, SchemaField):
                if key not in result and field_schema.default is not None:
                    result[key] = deepcopy(field_schema.default)
            elif isinstance(field_schema, dict):
                if key in result and isinstance(result[key], dict):
                    result[key] = self._apply_defaults(result[key], field_schema, field_path)
                elif key not in result:
                    nested_defaults = self._extract_nested_defaults(field_schema, field_path)
                    if nested_defaults:
                        result[key] = nested_defaults
        
        return result
    
    def _extract_nested_defaults(
        self,
        schema: Dict[str, Union[SchemaField, Dict]],
        path: str,
    ) -> Dict[str, Any]:
        """Extract default values from nested schema."""
        defaults = {}
        
        for key, field_schema in schema.items():
            if isinstance(field_schema, SchemaField):
                if field_schema.default is not None:
                    defaults[key] = deepcopy(field_schema.default)
            elif isinstance(field_schema, dict):
                nested = self._extract_nested_defaults(field_schema, f"{path}.{key}")
                if nested:
                    defaults[key] = nested
        
        return defaults
    
    def _validate(
        self,
        config: Any,
        schema: Dict[str, Union[SchemaField, Dict]],
        path: str,
    ) -> None:
        """Recursively validate configuration against schema."""
        if not isinstance(config, dict):
            self.errors.append(ValidationError(
                error_type=ValidationErrorType.TYPE_MISMATCH,
                path=path or "root",
                message="Expected a dictionary",
                expected="dict",
                actual=type(config).__name__,
            ))
            return
        
        for key, field_schema in schema.items():
            field_path = f"{path}.{key}" if path else key
            
            if isinstance(field_schema, SchemaField):
                self._validate_field(config, key, field_schema, field_path)
            elif isinstance(field_schema, dict):
                if key in config:
                    if isinstance(config[key], dict):
                        self._validate(config[key], field_schema, field_path)
                    else:
                        self.errors.append(ValidationError(
                            error_type=ValidationErrorType.TYPE_MISMATCH,
                            path=field_path,
                            message="Expected a nested dictionary",
                            expected="dict",
                            actual=type(config[key]).__name__,
                        ))
                elif self._is_required_nested_field(field_schema):
                    self.errors.append(ValidationError(
                        error_type=ValidationErrorType.MISSING_FIELD,
                        path=field_path,
                        message="Required nested configuration missing",
                    ))
        
        if not self.allow_extra_fields:
            for key in config:
                if key not in schema:
                    field_path = f"{path}.{key}" if path else key
                    self.errors.append(ValidationError(
                        error_type=ValidationErrorType.EXTRA_FIELD,
                        path=field_path,
                        message=f"Unexpected field '{key}' found in configuration",
                    ))
    
    def _is_required_nested_field(self, schema: Dict) -> bool:
        """Check if any field in nested schema is required."""
        for value in schema.values():
            if isinstance(value, SchemaField) and value.required:
                return True
            elif isinstance(value, dict) and self._is_required_nested_field(value):
                return True
        return False
    
    def _validate_field(
        self,
        config: Dict[str, Any],
        key: str,
        field: SchemaField,
        path: str,
    ) -> None:
        """Validate a single field against its schema."""
        if key not in config:
            if field.required:
                self.errors.append(ValidationError(
                    error_type=ValidationErrorType.MISSING_FIELD,
                    path=path,
                    message=f"Required field '{key}' is missing",
                ))
            return
        
        value = config[key]
        
        if not self._check_type(value, field.field_type):
            self.errors.append(ValidationError(
                error_type=ValidationErrorType.TYPE_MISMATCH,
                path=path,
                message=f"Type mismatch for field '{key}'",
                expected=" or ".join(t.__name__ for t in field.field_type),
                actual=type(value).__name__,
            ))
            return
        
        if field.allowed_values is not None and value not in field.allowed_values:
            self.errors.append(ValidationError(
                error_type=ValidationErrorType.INVALID_VALUE,
                path=path,
                message=f"Value not in allowed values for field '{key}'",
                expected=field.allowed_values,
                actual=value,
            ))
        
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if field.min_value is not None and value < field.min_value:
                self.errors.append(ValidationError(
                    error_type=ValidationErrorType.INVALID_VALUE,
                    path=path,
                    message=f"Value below minimum for field '{key}'",
                    expected=f">= {field.min_value}",
                    actual=value,
                ))
            
            if field.max_value is not None and value > field.max_value:
                self.errors.append(ValidationError(
                    error_type=ValidationErrorType.INVALID_VALUE,
                    path=path,
                    message=f"Value above maximum for field '{key}'",
                    expected=f"<= {field.max_value}",
                    actual=value,
                ))
        
        if isinstance(value, (str, list)):
            length = len(value)
            
            if field.min_length is not None and length < field.min_length:
                self.errors.append(ValidationError(
                    error_type=ValidationErrorType.INVALID_VALUE,
                    path=path,
                    message=f"Length below minimum for field '{key}'",
                    expected=f">= {field.min_length}",
                    actual=length,
                ))
            
            if field.max_length is not None and length > field.max_length:
                self.errors.append(ValidationError(
                    error_type=ValidationErrorType.INVALID_VALUE,
                    path=path,
                    message=f"Length above maximum for field '{key}'",
                    expected=f"<= {field.max_length}",
                    actual=length,
                ))
        
        if isinstance(value, str) and field.pattern is not None:
            if not re.fullmatch(field.pattern, value):
                self.errors.append(ValidationError(
                    error_type=ValidationErrorType.INVALID_VALUE,
                    path=path,
                    message=f"Value does not match required pattern for field '{key}'",
                    expected=f"pattern: {field.pattern}",
                    actual=value,
                ))
        
        if isinstance(value, list) and field.item_schema is not None:
            for i, item in enumerate(value):
                item_path = f"{path}[{i}]"
                if isinstance(field.item_schema, SchemaField):
                    temp_config = {'_item': item}
                    self._validate_field(temp_config, '_item', field.item_schema, item_path)
                elif isinstance(field.item_schema, dict):
                    if isinstance(item, dict):
                        self._validate(item, field.item_schema, item_path)
                    else:
                        self.errors.append(ValidationError(
                            error_type=ValidationErrorType.TYPE_MISMATCH,
                            path=item_path,
                            message="Expected a dictionary for list item",
                            expected="dict",
                            actual=type(item).__name__,
                        ))
    
    def _check_type(self, value: Any, types: List[Type[Any]]) -> bool:
        """Check if value matches any of the allowed types, handling bool/int correctly."""
        for t in types:
            if t is bool:
                if isinstance(value, bool):
                    return True
            elif t is int:
                if isinstance(value, int) and not isinstance(value, bool):
                    return True
            elif isinstance(value, t):
                return True
        return False


def create_schema(schema_dict: Dict[str, Any]) -> ConfigSchema:
    """
    Create a ConfigSchema from a dictionary specification.
    
    Args:
        schema_dict: Dictionary defining the schema structure
        
    Returns:
        ConfigSchema instance
    """
    return ConfigSchema(schema_dict)