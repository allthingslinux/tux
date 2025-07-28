# Input Validation Standardization Plan

## Overview

This document provides a detailed plan for standardizing input validation across the Tux Discord bot codebase. The goal is to create a comprehensive, reusable validation framework that ensures all user inputs are properly validated and sanitized before processing.

## Current State Analysis

### Existing Validation Mechanisms

1. **Harmful Command Detection** (`tux/utils/functions.py`)
   - `is_harmful()` function detects dangerous system commands
   - Covers fork bombs, rm commands, dd commands, and format commands
   - Limited scope focused on system-level threats

2. **Content Sanitization** (`tux/utils/functions.py`)
   - `strip_formatting()` removes markdown formatting
   - Basic regex-based sanitization
   - Used in event handlers for content processing

3. **Discord.py Built-in Validation**
   - Type converters for Discord objects (User, Channel, Role)
   - Basic parameter validation through command decorators
   - Limited to Discord-specific object validation

### Validation Gaps

1. **Inconsistent Application**: Validation not applied uniformly across all commands
2. **Limited Scope**: Current validation focuses on specific threat types
3. **No Centralized Framework**: Validation logic scattered across codebase
4. **Missing Validation Types**: No validation for URLs, file uploads, complex data structures
5. **Poor Error Handling**: Inconsistent error messages and handling for validation failures

## Validation Framework Design

### Core Architecture

```python
# tux/security/validation/__init__.py
from .engine import ValidationEngine
from .decorators import validate_input, validate_output
from .validators import *
from .sanitizers import SanitizationPipeline
from .exceptions import ValidationError, SanitizationError

__all__ = [
    "ValidationEngine",
    "validate_input", 
    "validate_output",
    "SanitizationPipeline",
    "ValidationError",
    "SanitizationError"
]
```

### Validation Engine

```python
# tux/security/validation/engine.py
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

class ValidationType(Enum):
    TEXT = "text"
    URL = "url"
    DISCORD_ID = "discord_id"
    EMAIL = "email"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    COMMAND = "command"
    FILE_PATH = "file_path"

@dataclass
class ValidationRule:
    validator_type: ValidationType
    required: bool = True
    max_length: Optional[int] = None
    min_length: Optional[int] = None
    pattern: Optional[str] = None
    allowed_values: Optional[List[Any]] = None
    custom_validator: Optional[callable] = None
    sanitize: bool = True

class ValidationResult:
    def __init__(self, is_valid: bool, value: Any = None, errors: List[str] = None):
        self.is_valid = is_valid
        self.value = value
        self.errors = errors or []

class ValidationEngine:
    def __init__(self):
        self.validators = self._initialize_validators()
        self.sanitizers = SanitizationPipeline()
    
    def validate(self, value: Any, rule: ValidationRule) -> ValidationResult:
        """Main validation method that applies all relevant checks."""
        try:
            # Step 1: Basic type and requirement checks
            if not self._check_required(value, rule.required):
                return ValidationResult(False, None, ["Field is required"])
            
            if value is None and not rule.required:
                return ValidationResult(True, None)
            
            # Step 2: Apply sanitization if enabled
            if rule.sanitize:
                value = self.sanitizers.sanitize(value, rule.validator_type)
            
            # Step 3: Apply specific validator
            validator = self.validators.get(rule.validator_type)
            if not validator:
                return ValidationResult(False, value, [f"Unknown validator type: {rule.validator_type}"])
            
            result = validator.validate(value, rule)
            return result
            
        except Exception as e:
            return ValidationResult(False, value, [f"Validation error: {str(e)}"])
```

### Validator Implementations

```python
# tux/security/validation/validators/text.py
import re
from typing import List
from ..engine import ValidationRule, ValidationResult

class TextValidator:
    def __init__(self):
        self.dangerous_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',               # JavaScript URLs
            r'data:text/html',           # Data URLs with HTML
            r'vbscript:',                # VBScript URLs
        ]
    
    def validate(self, value: str, rule: ValidationRule) -> ValidationResult:
        errors = []
        
        # Length validation
        if rule.max_length and len(value) > rule.max_length:
            errors.append(f"Text exceeds maximum length of {rule.max_length}")
        
        if rule.min_length and len(value) < rule.min_length:
            errors.append(f"Text is shorter than minimum length of {rule.min_length}")
        
        # Pattern validation
        if rule.pattern and not re.match(rule.pattern, value):
            errors.append("Text does not match required pattern")
        
        # Dangerous content detection
        for pattern in self.dangerous_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                errors.append("Text contains potentially dangerous content")
                break
        
        # Allowed values check
        if rule.allowed_values and value not in rule.allowed_values:
            errors.append(f"Value must be one of: {', '.join(rule.allowed_values)}")
        
        return ValidationResult(len(errors) == 0, value, errors)

# tux/security/validation/validators/url.py
import re
from urllib.parse import urlparse
from typing import List, Set
from ..engine import ValidationRule, ValidationResult

class URLValidator:
    def __init__(self):
        self.allowed_schemes = {'http', 'https'}
        self.blocked_domains = {
            'malicious-site.com',
            'phishing-example.org',
            # Add known malicious domains
        }
        self.url_shorteners = {
            'bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly'
        }
    
    def validate(self, value: str, rule: ValidationRule) -> ValidationResult:
        errors = []
        
        try:
            parsed = urlparse(value)
            
            # Scheme validation
            if parsed.scheme not in self.allowed_schemes:
                errors.append(f"URL scheme must be one of: {', '.join(self.allowed_schemes)}")
            
            # Domain validation
            if parsed.netloc.lower() in self.blocked_domains:
                errors.append("URL domain is blocked")
            
            # URL shortener detection
            if parsed.netloc.lower() in self.url_shorteners:
                errors.append("URL shorteners are not allowed")
            
            # Custom domain allowlist
            if hasattr(rule, 'allowed_domains') and rule.allowed_domains:
                if parsed.netloc.lower() not in [d.lower() for d in rule.allowed_domains]:
                    errors.append(f"URL domain must be one of: {', '.join(rule.allowed_domains)}")
            
        except Exception as e:
            errors.append(f"Invalid URL format: {str(e)}")
        
        return ValidationResult(len(errors) == 0, value, errors)

# tux/security/validation/validators/discord_id.py
import re
from ..engine import ValidationRule, ValidationResult

class DiscordIDValidator:
    def __init__(self):
        # Discord snowflake pattern (17-19 digits)
        self.snowflake_pattern = re.compile(r'^\d{17,19}$')
    
    def validate(self, value: str, rule: ValidationRule) -> ValidationResult:
        errors = []
        
        # Convert to string if integer
        if isinstance(value, int):
            value = str(value)
        
        # Pattern validation
        if not self.snowflake_pattern.match(value):
            errors.append("Invalid Discord ID format")
        
        # Range validation (Discord epoch started 2015-01-01)
        try:
            snowflake = int(value)
            if snowflake < 175928847299117063:  # Approximate Discord epoch
                errors.append("Discord ID predates Discord epoch")
        except ValueError:
            errors.append("Discord ID must be numeric")
        
        return ValidationResult(len(errors) == 0, value, errors)
```

### Sanitization Pipeline

```python
# tux/security/validation/sanitizers.py
import re
import html
from typing import Any
from .engine import ValidationType

class SanitizationPipeline:
    def __init__(self):
        self.sanitizers = {
            ValidationType.TEXT: self._sanitize_text,
            ValidationType.URL: self._sanitize_url,
            ValidationType.COMMAND: self._sanitize_command,
        }
    
    def sanitize(self, value: Any, validation_type: ValidationType) -> Any:
        """Apply appropriate sanitization based on validation type."""
        sanitizer = self.sanitizers.get(validation_type)
        if sanitizer:
            return sanitizer(value)
        return value
    
    def _sanitize_text(self, text: str) -> str:
        """Sanitize text content."""
        # HTML entity encoding
        text = html.escape(text)
        
        # Remove/escape markdown formatting if needed
        text = self._sanitize_markdown(text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove control characters except newlines and tabs
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        return text
    
    def _sanitize_markdown(self, text: str) -> str:
        """Sanitize markdown formatting."""
        # Remove triple backtick blocks
        text = re.sub(r'```(.*?)```', r'\1', text, flags=re.DOTALL)
        
        # Remove single backtick code blocks
        text = re.sub(r'`([^`]*)`', r'\1', text)
        
        # Remove markdown headers
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
        
        # Remove markdown formatting characters
        text = re.sub(r'[\*_~>]', '', text)
        
        return text
    
    def _sanitize_url(self, url: str) -> str:
        """Sanitize URL content."""
        # Remove whitespace
        url = url.strip()
        
        # Ensure proper encoding
        # Note: More sophisticated URL sanitization would go here
        
        return url
    
    def _sanitize_command(self, command: str) -> str:
        """Sanitize command input."""
        # Remove dangerous characters
        command = re.sub(r'[;&|`$()]', '', command)
        
        # Normalize whitespace
        command = re.sub(r'\s+', ' ', command).strip()
        
        return command
```

### Validation Decorators

```python
# tux/security/validation/decorators.py
from functools import wraps
from typing import Dict, Any, Callable
from discord.ext import commands
from .engine import ValidationEngine, ValidationRule, ValidationType
from .exceptions import ValidationError

def validate_input(**field_rules: Dict[str, ValidationRule]):
    """Decorator to validate command inputs."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            engine = ValidationEngine()
            
            # Get the context (first argument for commands)
            ctx = args[0] if args else None
            
            # Validate each specified field
            for field_name, rule in field_rules.items():
                if field_name in kwargs:
                    value = kwargs[field_name]
                    result = engine.validate(value, rule)
                    
                    if not result.is_valid:
                        error_msg = f"Validation failed for {field_name}: {'; '.join(result.errors)}"
                        if isinstance(ctx, commands.Context):
                            await ctx.send(f"❌ {error_msg}")
                            return
                        else:
                            raise ValidationError(error_msg)
                    
                    # Update with sanitized value
                    kwargs[field_name] = result.value
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Convenience decorators for common validation patterns
def validate_text(field: str, max_length: int = None, required: bool = True):
    """Validate text input."""
    rule = ValidationRule(
        validator_type=ValidationType.TEXT,
        required=required,
        max_length=max_length
    )
    return validate_input(**{field: rule})

def validate_url(field: str, allowed_domains: list = None, required: bool = True):
    """Validate URL input."""
    rule = ValidationRule(
        validator_type=ValidationType.URL,
        required=required
    )
    if allowed_domains:
        rule.allowed_domains = allowed_domains
    return validate_input(**{field: rule})

def validate_discord_id(field: str, required: bool = True):
    """Validate Discord ID input."""
    rule = ValidationRule(
        validator_type=ValidationType.DISCORD_ID,
        required=required
    )
    return validate_input(**{field: rule})
```

## Implementation Plan

### Phase 1: Core Framework (Week 1-2)

1. **Create validation module structure**

   ```
   tux/security/
   ├── __init__.py
   ├── validation/
   │   ├── __init__.py
   │   ├── engine.py
   │   ├── decorators.py
   │   ├── sanitizers.py
   │   ├── exceptions.py
   │   └── validators/
   │       ├── __init__.py
   │       ├── text.py
   │       ├── url.py
   │       ├── discord_id.py
   │       ├── command.py
   │       └── file.py
   ```

2. **Implement core validation engine**
3. **Create basic validators** (text, URL, Discord ID)
4. **Implement sanitization pipeline**
5. **Add comprehensive unit tests**

### Phase 2: Decorator System (Week 3)

1. **Implement validation decorators**
2. **Create convenience decorators** for common patterns
3. **Add integration with Discord.py command system**
4. **Test decorator functionality** with sample commands

### Phase 3: Migration Strategy (Week 4-6)

1. **Identify high-priority commands** for migration
2. **Create migration guidelines** for developers
3. **Migrate critical security-sensitive commands** first
4. **Gradually migrate remaining commands**
5. **Update documentation** with new patterns

### Phase 4: Advanced Features (Week 7-8)

1. **Implement file validation** for uploads
2. **Add JSON/structured data validation**
3. **Create custom validator support**
4. **Add validation caching** for performance
5. **Implement validation metrics** and monitoring

## Usage Examples

### Basic Text Validation

```python
from tux.security.validation import validate_text

class ExampleCog(commands.Cog):
    @commands.command()
    @validate_text("message", max_length=2000)
    async def say(self, ctx: commands.Context, *, message: str):
        """Say something with validated input."""
        await ctx.send(message)
```

### URL Validation

```python
from tux.security.validation import validate_url

class LinkCog(commands.Cog):
    @commands.command()
    @validate_url("url", allowed_domains=["github.com", "docs.python.org"])
    async def link(self, ctx: commands.Context, url: str):
        """Share a link with domain validation."""
        await ctx.send(f"Here's your link: {url}")
```

### Complex Validation

```python
from tux.security.validation import validate_input, ValidationRule, ValidationType

class ConfigCog(commands.Cog):
    @commands.command()
    @validate_input(
        channel_id=ValidationRule(ValidationType.DISCORD_ID, required=True),
        message=ValidationRule(ValidationType.TEXT, max_length=1000, required=False)
    )
    async def config_channel(self, ctx: commands.Context, channel_id: str, message: str = None):
        """Configure channel with validated inputs."""
        # Implementation here
        pass
```

## Testing Strategy

### Unit Tests

1. **Validator Tests**: Test each validator with valid/invalid inputs
2. **Sanitizer Tests**: Verify sanitization removes dangerous content
3. **Engine Tests**: Test validation engine with various rule combinations
4. **Decorator Tests**: Test decorator integration with commands

### Integration Tests

1. **Command Integration**: Test validators with actual Discord commands
2. **Performance Tests**: Ensure validation doesn't impact bot performance
3. **Error Handling**: Test validation error scenarios
4. **Edge Cases**: Test with malformed, empty, and boundary inputs

### Security Tests

1. **Bypass Attempts**: Test for validation bypass vulnerabilities
2. **Injection Tests**: Test for various injection attack vectors
3. **DoS Tests**: Test validation performance under load
4. **Fuzzing**: Automated testing with random inputs

## Performance Considerations

### Optimization Strategies

1. **Caching**: Cache validation results for repeated inputs
2. **Lazy Loading**: Load validators only when needed
3. **Async Validation**: Use async patterns for expensive validations
4. **Batch Processing**: Validate multiple inputs together when possible

### Monitoring

1. **Validation Metrics**: Track validation success/failure rates
2. **Performance Metrics**: Monitor validation execution time
3. **Error Tracking**: Log validation errors for analysis
4. **Usage Analytics**: Track which validators are used most

## Migration Guidelines

### For Developers

1. **Identify Input Points**: Find all user input in your commands
2. **Choose Appropriate Validators**: Select validators based on input type
3. **Add Decorators**: Apply validation decorators to commands
4. **Test Thoroughly**: Verify validation works as expected
5. **Update Documentation**: Document validation requirements

### Migration Priority

1. **High Priority**: Admin commands, moderation commands, configuration
2. **Medium Priority**: User-facing commands with text input
3. **Low Priority**: Simple commands with minimal input

### Backward Compatibility

1. **Gradual Migration**: Migrate commands incrementally
2. **Fallback Support**: Maintain old validation during transition
3. **Warning System**: Warn about deprecated validation patterns
4. **Documentation**: Provide clear migration examples

## Success Metrics

### Security Improvements

- **Input Coverage**: 100% of user inputs validated
- **Vulnerability Reduction**: 90% reduction in input-related vulnerabilities
- **Attack Prevention**: Block 99% of known attack patterns

### Developer Experience

- **Adoption Rate**: 80% of developers using new validation system
- **Development Speed**: No significant impact on development velocity
- **Error Reduction**: 50% reduction in input-related bugs

### Performance

- **Response Time**: < 10ms additional latency for validation
- **Memory Usage**: < 5% increase in memory consumption
- **CPU Usage**: < 2% increase in CPU usage

This comprehensive input validation standardization plan provides a robust foundation for securing user inputs across the Tux Discord bot while maintaining developer productivity and system performance.
