import json
import os
import re
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional, Union
import yaml
from jsonschema import Draft7Validator, ValidationError as JsonSchemaValidationError, SchemaError


class ConfigError(Exception):
    """Base exception for configuration errors."""
    pass


class ValidationError(ConfigError):
    """Exception raised when configuration validation fails."""
    pass


class SecurityError(ConfigError):
    """Exception raised for security-related issues."""
    pass


class ConfigLoader:
    """Configuration loader with validation, interpolation, and error handling."""
    
    _schema_cache: Dict[str, Draft7Validator] = {}
    _env_var_pattern = re.compile(r'\$\{([A-Z_][A-Z0-9_]*?)(?::-(.*?))?\}')
    _max_file_size = 10 * 1024 * 1024  # 10MB
    
    def __init__(self, allowed_directory: Optional[Path] = None):
        """Initialize the config loader.
        
        Args:
            allowed_directory: Optional directory to restrict file access to.
        """
        self.allowed_directory = allowed_directory
    
    def load_config(
        self,
        filepath: str,
        schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Load and validate a configuration file.
        
        Args:
            filepath: Path to the configuration file (.json, .yaml, or .yml)
            schema: Optional JSON Schema to validate against
            
        Returns:
            Validated configuration dictionary
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            PermissionError: If config file cannot be read
            ConfigError: If config is invalid or cannot be parsed
            ValidationError: If config doesn't match schema
            SecurityError: If path validation fails
        """
        # Validate and sanitize file path
        resolved_path = self._validate_path(filepath)
        
        # Check file size
        self._check_file_size(resolved_path)
        
        # Load configuration file
        config = self._load_file(resolved_path)
        
        # Handle empty files
        if config is None:
            config = {}
        
        # Perform environment variable interpolation
        config = self._interpolate_env_vars(config)
        
        # Validate against schema if provided
        if schema is not None:
            self._validate_schema(schema)
            config = self._apply_defaults(config, schema)
            self._validate_config(config, schema)
        
        return config
    
    def _validate_path(self, filepath: str) -> Path:
        """Validate and sanitize file path to prevent directory traversal.
        
        Args:
            filepath: Path to validate
            
        Returns:
            Resolved Path object
            
        Raises:
            SecurityError: If path is invalid or outside allowed directory
        """
        if '..' in filepath:
            raise SecurityError('Path traversal detected')
        
        path = Path(filepath).resolve()
        
        if self.allowed_directory is not None:
            allowed = Path(self.allowed_directory).resolve()
            try:
                path.relative_to(allowed)
            except ValueError:
                raise SecurityError('Path outside allowed directory')
        
        return path
    
    def _check_file_size(self, path: Path) -> None:
        """Check that file size is within limits.
        
        Args:
            path: Path to check
            
        Raises:
            ConfigError: If file is too large
        """
        try:
            file_size = path.stat().st_size
            if file_size > self._max_file_size:
                raise ConfigError(
                    f'Config file too large: {file_size} bytes exceeds 10MB limit'
                )
        except OSError as e:
            raise ConfigError(f'Cannot check file size: {e}')
    
    def _load_file(self, path: Path) -> Dict[str, Any]:
        """Load configuration file based on extension.
        
        Args:
            path: Path to configuration file
            
        Returns:
            Parsed configuration dictionary
            
        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If file cannot be read
            ConfigError: If file cannot be parsed
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                if not content.strip():
                    return {}
                
                if path.suffix == '.json':
                    return self._load_json(content, str(path))
                elif path.suffix in ('.yaml', '.yml'):
                    return self._load_yaml(content, str(path))
                else:
                    raise ConfigError(
                        f'Unsupported file extension: {path.suffix}. '
                        'Use .json, .yaml, or .yml'
                    )
        except FileNotFoundError:
            raise FileNotFoundError(f'Config file not found: {path}')
        except PermissionError:
            raise PermissionError(f'Permission denied reading config file: {path}')
    
    def _load_json(self, content: str, filename: str) -> Dict[str, Any]:
        """Load JSON content.
        
        Args:
            content: JSON string content
            filename: Filename for error messages
            
        Returns:
            Parsed JSON dictionary
            
        Raises:
            ConfigError: If JSON is malformed
        """
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            # Try YAML to detect format mismatch
            try:
                yaml.safe_load(content)
                raise ConfigError(
                    f'{filename} has .json extension but content may be YAML'
                )
            except yaml.YAMLError:
                pass
            
            raise ConfigError(
                f'JSON syntax error in {filename} at line {e.lineno}, '
                f'column {e.colno}: {e.msg}'
            )
    
    def _load_yaml(self, content: str, filename: str) -> Dict[str, Any]:
        """Load YAML content.
        
        Args:
            content: YAML string content
            filename: Filename for error messages
            
        Returns:
            Parsed YAML dictionary
            
        Raises:
            ConfigError: If YAML is malformed
        """
        try:
            data = yaml.safe_load(content)
            if data is None:
                data = {}
            return data
        except yaml.YAMLError as e:
            # Try JSON to detect format mismatch
            try:
                json.loads(content)
                raise ConfigError(
                    f'{filename} has .yaml extension but content may be JSON'
                )
            except json.JSONDecodeError:
                pass
            
            mark = getattr(e, 'problem_mark', None)
            location = f' at line {mark.line + 1}' if mark else ''
            raise ConfigError(f'YAML syntax error in {filename}{location}')
    
    def _interpolate_env_vars(self, obj: Any) -> Any:
        """Recursively interpolate environment variables.
        
        Args:
            obj: Object to interpolate (dict, list, string, or other)
            
        Returns:
            Object with environment variables interpolated
            
        Raises:
            ConfigError: If required environment variable is not set
        """
        if isinstance(obj, dict):
            return {k: self._interpolate_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._interpolate_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            return self._replace_env_vars(obj)
        else:
            return obj
    
    def _replace_env_vars(self, value: str) -> str:
        """Replace environment variable references in a string.
        
        Args:
            value: String potentially containing ${VAR} or ${VAR:-default}
            
        Returns:
            String with environment variables replaced
            
        Raises:
            ConfigError: If required environment variable is not set
        """
        def replacer(match: re.Match) -> str:
            var_name = match.group(1)
            default_value = match.group(2)
            
            if var_name in os.environ:
                return os.environ[var_name]
            elif default_value is not None:
                return default_value
            else:
                raise ConfigError(
                    f'Environment variable "{var_name}" is not set'
                )
        
        return self._env_var_pattern.sub(replacer, value)
    
    def _validate_schema(self, schema: Dict[str, Any]) -> None:
        """Validate that schema itself is valid.
        
        Args:
            schema: JSON Schema to validate
            
        Raises:
            SchemaError: If schema is invalid
        """
        try:
            Draft7Validator.check_schema(schema)
        except JsonSchemaValidationError as e:
            raise SchemaError(f'Invalid schema: {e.message}')
    
    def _get_cached_validator(self, schema: Dict[str, Any]) -> Draft7Validator:
        """Get or create a cached validator for the schema.
        
        Args:
            schema: JSON Schema
            
        Returns:
            Cached or new Draft7Validator instance
        """
        schema_str = json.dumps(schema, sort_keys=True)
        schema_hash = hashlib.sha256(schema_str.encode()).hexdigest()
        
        if schema_hash not in self._schema_cache:
            self._schema_cache[schema_hash] = Draft7Validator(schema)
        
        return self._schema_cache[schema_hash]
    
    def _apply_defaults(
        self,
        config: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply default values from schema to config.
        
        Args:
            config: Configuration dictionary
            schema: JSON Schema with default values
            
        Returns:
            Configuration with defaults applied
        """
        import copy
        result = copy.deepcopy(config)
        
        if 'properties' in schema:
            for prop_name, prop_schema in schema['properties'].items():
                if prop_name not in result and 'default' in prop_schema:
                    result[prop_name] = prop_schema['default']
                elif prop_name in result and isinstance(result[prop_name], dict):
                    if prop_schema.get('type') == 'object':
                        result[prop_name] = self._apply_defaults(
                            result[prop_name],
                            prop_schema
                        )
        
        return result
    
    def _validate_config(
        self,
        config: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> None:
        """Validate configuration against schema.
        
        Args:
            config: Configuration to validate
            schema: JSON Schema to validate against
            
        Raises:
            ValidationError: If validation fails
        """
        # Type coercion before validation
        config = self._coerce_types(config, schema)
        
        validator = self._get_cached_validator(schema)
        errors = list(validator.iter_errors(config))
        
        if errors:
            messages = []
            for error in errors:
                path = '.'.join(str(p) for p in error.path) if error.path else 'root'
                messages.append(f'{path}: {error.message}')
            
            raise ValidationError(
                f'Config validation failed:\n' + '\n'.join(messages)
            )
    
    def _coerce_types(
        self,
        config: Any,
        schema: Dict[str, Any]
    ) -> Any:
        """Coerce string values from environment variables to schema types.
        
        Args:
            config: Configuration to coerce
            schema: Schema defining expected types
            
        Returns:
            Configuration with types coerced
            
        Raises:
            ConfigError: If type coercion fails
        """
        import copy
        
        if not isinstance(config, dict):
            return config
        
        result = copy.deepcopy(config)
        
        if 'properties' in schema:
            for prop_name, prop_schema in schema['properties'].items():
                if prop_name in result:
                    result[prop_name] = self._coerce_value(
                        result[prop_name],
                        prop_schema,
                        f'{prop_name}'
                    )
        
        return result
    
    def _coerce_value(
        self,
        value: Any,
        schema: Dict[str, Any],
        path: str
    ) -> Any:
        """Coerce a single value to the schema type.
        
        Args:
            value: Value to coerce
            schema: Schema for this value
            path: JSON path for error messages
            
        Returns:
            Coerced value
            
        Raises:
            ConfigError: If coercion fails
        """
        schema_type = schema.get('type')
        
        if schema_type == 'number' and isinstance(value, str):
            try:
                return float(value) if '.' in value else int(value)
            except ValueError:
                raise ConfigError(
                    f'Environment variable at "{path}" has invalid value '
                    f'for expected type: number'
                )
        
        elif schema_type == 'integer' and isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                raise ConfigError(
                    f'Environment variable at "{path}" has invalid value '
                    f'for expected type: integer'
                )
        
        elif schema_type == 'boolean' and isinstance(value, str):
            lower_value = value.lower()
            if lower_value in ('true', '1', 'yes'):
                return True
            elif lower_value in ('false', '0', 'no'):
                return False
            else:
                raise ConfigError(
                    f'Environment variable at "{path}" has invalid value '
                    f'for expected type: boolean'
                )
        
        elif schema_type == 'object' and isinstance(value, dict):
            return self._coerce_types(value, schema)
        
        elif schema_type == 'array' and isinstance(value, list):
            items_schema = schema.get('items', {})
            return [
                self._coerce_value(item, items_schema, f'{path}[{i}]')
                for i, item in enumerate(value)
            ]
        
        return value


def load_config(
    filepath: str,
    schema: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Load and validate a configuration file.
    
    Convenience function that creates a ConfigLoader and loads a config file.
    
    Args:
        filepath: Path to the configuration file (.json, .yaml, or .yml)
        schema: Optional JSON Schema to validate against
        
    Returns:
        Validated configuration dictionary
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        PermissionError: If config file cannot be read
        ConfigError: If config is invalid or cannot be parsed
        ValidationError: If config doesn't match schema
        SecurityError: If path validation fails
    """
    loader = ConfigLoader()
    return loader.load_config(filepath, schema)