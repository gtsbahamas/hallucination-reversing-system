import os
import re
import json
import yaml
from typing import Any, Dict, List, Optional, Union, Type
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


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
        field_type: Union[Type, List[Type]],
        required: bool = True,
        default: Any = None,
        allowed_values: Optional[List[Any]] = None,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        description: Optional[str] = None,
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


class ConfigSchema:
    """Defines the schema for configuration validation."""
    
    def __init__(self, schema: Dict[str, Union[SchemaField, Dict]]):
        self.schema = schema
    
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
    
    def __init__(
        self,
        schema: Optional[ConfigSchema] = None,
        strict: bool = True,
        allow_extra_fields: bool = False,
    ):
        self.schema = schema
        self.strict = strict
        self.allow_extra_fields = allow_extra_fields
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
            ValueError: If the file format is not supported
        """
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        config_type = self._detect_config_type(config_path)
        raw_config = self._load_file(config_path, config_type)
        config = self._interpolate_env_vars(raw_config)
        
        if self.schema:
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
        config = self._interpolate_env_vars(config)
        
        if self.schema:
            self.errors = []
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
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_type == ConfigType.YAML:
                return yaml.safe_load(f) or {}
            else:
                return json.load(f)
    
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
                var_name, default = var_expr.split(':', 1)
                return os.getenv(var_name.strip(), default.strip())
            else:
                var_name = var_expr.strip()
                env_value = os.getenv(var_name)
                
                if env_value is None and self.strict:
                    self.errors.append(ValidationError(
                        error_type=ValidationErrorType.ENV_VAR_NOT_FOUND,
                        path=path,
                        message=f"Environment variable '{var_name}' not found and no default provided",
                    ))
                    return match.group(0)
                
                return env_value or match.group(0)
        
        return self.ENV_VAR_PATTERN.sub(replace_env_var, value)
    
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
            elif field.default is not None:
                config[key] = field.default
            return
        
        value = config[key]
        
        if not any(isinstance(value, t) for t in field.field_type):
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
        
        if isinstance(value, (int, float)):
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
            if not re.match(field.pattern, value):
                self.errors.append(ValidationError(
                    error_type=ValidationErrorType.INVALID_VALUE,
                    path=path,
                    message=f"Value does not match required pattern for field '{key}'",
                    expected=f"pattern: {field.pattern}",
                    actual=value,
                ))


def create_schema(schema_dict: Dict[str, Any]) -> ConfigSchema:
    """
    Create a ConfigSchema from a dictionary specification.
    
    Args:
        schema_dict: Dictionary defining the schema structure
        
    Returns:
        ConfigSchema instance
    """
    return ConfigSchema(schema_dict)