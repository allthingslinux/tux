# User-Friendly Error Message System Design

## Overview

This document outlines the design for a comprehensive user-friendly error message system that provides clear, actionable, and contextually appropriate error messages to Discord bot users while maintaining technical accuracy for developers.

## Current State Analysis

### Existing Message Patterns

The current system has good foundation with:

- Structured error messages in `ERROR_CONFIG_MAP`
- Context-aware message formatting
- Consistent embed styling
- Sentry ID inclusion for support

### Areas for Improvement

- **Inconsistent Tone**: Messages vary in formality and helpfulness
- **Limited Guidance**: Many errors lack actionable next steps
- **No Localization**: Single language support only
- **Missing Context**: Some err't explain why they occurred
- **Poor Progressive Disclosure**: All details shown at once

## Message Design Principles

### 1. Clarity and Simplicity

- Use plain language, avoid technical jargon
- Keep messages concise but informative
- Structure information hierarchically

### 2. Actionability

- Always provide next steps when possible
- Include specific commands or actions to resolve issues
- Link to relevant help resources

### 3. Contextual Appropriateness

- Tailor message detail to user's permission level
- Consider the command context and user intent
- Adapt tone to error severity

### 4. Consistency

- Standardized message structure across all errors
- Consistent terminology and formatting
- Unified visual presentation

## Message Template System

### Template Structure

```python
@dataclass
class ErrorMessageTemplate:
    """Template for generating user-friendly error messages."""
    
    # Core message components
    title: str                          # Brief error title
    description: str                    # Main error explanation
    reason: str | None = None          # Why the error occurred
    solution: str | None = None        # How to fix it
    help_command: str | None = None    # Relevant help command
    
    # Message metadata
    severity: ErrorSeverity            # Error severity level
    category: ErrorCategory            # Error category
    user_facing: bool = True           # Whether to show to users
    
    # Customization options
    include_sentry_id: bool = True     # Include error ID
    include_help_footer: bool = True   # Include help footer
    ephemeral: bool = False            # Send as ephemeral message
    
    # Localization support
    locale_key: str | None = None      # Localization key
    
    def format(self, **kwargs) -> FormattedErrorMessage:
        """Format the template with provided context."""
        # Implementation details...
```

### Message Categories and Templates

#### User Error Messages

```python
USER_ERROR_TEMPLATES = {
    'PERMISSION_DENIED': ErrorMessageTemplate(
        title="Permission Required",
        description="You don't have permission to use this command.",
        reason="This command requires the `{permission}` permission level.",
        solution="Contact a server administrator if you believe you should have access.",
        help_command="help permissions",
        severity=ErrorSeverity.USER,
        category=ErrorCategory.PERMISSION
    ),
    
    'INVALID_INPUT': ErrorMessageTemplate(
        title="Invalid Input",
        description="The input you provided is not valid.",
        reason="Expected: {expected_format}",
        solution="Please check your input and try again.",
        help_command="help {command_name}",
        severity=ErrorSeverity.USER,
        category=ErrorCategory.VALIDATION
    ),
    
    'MISSING_ARGUMENT': ErrorMessageTemplate(
        title="Missing Required Information",
        description="This command requires additional information to work.",
        reason="Missing required parameter: `{parameter_name}`",
        solution="Use `{prefix}help {command_name}` to see the correct usage.",
        help_command="help {command_name}",
        severity=ErrorSeverity.USER,
        category=ErrorCategory.VALIDATION
    ),
    
    'COOLDOWN_ACTIVE': ErrorMessageTemplate(
        title="Command on Cooldown",
        description="This command is temporarily unavailable.",
        reason="You can use this command again in {retry_after} seconds.",
        solution="Please wait and try again later.",
        severity=ErrorSeverity.USER,
        category=ErrorCategory.RATE_LIMIT,
        ephemeral=True
    )
}
```

#### System Error Messages

```python
SYSTEM_ERROR_TEMPLATES = {
    'DATABASE_ERROR': ErrorMessageTemplate(
        title="Service Temporarily Unavailable",
        description="We're experiencing technical difficulties.",
        reason="Our database service is currently unavailable.",
        solution="Please try again in a few moments. If this persists, contact support.",
        severity=ErrorSeverity.SYSTEM,
        category=ErrorCategory.DATABASE
    ),
    
    'CONFIGURATION_ERROR': ErrorMessageTemplate(
        title="Bot Configuration Issue",
        description="The bot is not properly set up for this server.",
        reason="Required configuration is missing or invalid.",
        solution="Please contact a server administrator to resolve this issue.",
        help_command="help setup",
        severity=ErrorSeverity.SYSTEM,
        category=ErrorCategory.CONFIGURATION
    ),
    
    'EXTERNAL_SERVICE_ERROR': ErrorMessageTemplate(
        title="External Service Unavailable",
        description="A service this command depends on is currently unavailable.",
        reason="The {service_name} service is not responding.",
        solution="This is usually temporary. Please try again later.",
        severity=ErrorSeverity.EXTERNAL,
        category=ErrorCategory.EXTERNAL_SERVICE
    )
}
```

#### Business Logic Error Messages

```python
BUSINESS_ERROR_TEMPLATES = {
    'RESOURCE_LIMIT_EXCEEDED': ErrorMessageTemplate(
        title="Limit Reached",
        description="You've reached the maximum allowed limit for this action.",
        reason="Current limit: {current_limit}, Maximum: {max_limit}",
        solution="You can try again after {reset_time} or upgrade your plan.",
        severity=ErrorSeverity.BUSINESS,
        category=ErrorCategory.BUSINESS_RULE
    ),
    
    'INVALID_OPERATION': ErrorMessageTemplate(
        title="Action Not Allowed",
        description="This action cannot be performed right now.",
        reason="{specific_reason}",
        solution="Please check the requirements and try again.",
        severity=ErrorSeverity.BUSINESS,
        category=ErrorCategory.BUSINESS_RULE
    )
}
```

## Message Formatting System

### Context-Aware Formatting

```python
class ErrorMessageFormatter:
    """Formats error messages with context-aware enhancements."""
    
    def __init__(self, bot: Tux):
        self.bot = bot
        self.templates = self._load_templates()
        self.localizer = MessageLocalizer()
    
    def format_error_message(
        self,
        template_key: str,
        context: ErrorContext,
        user_context: UserContext,
        **format_kwargs
    ) -> FormattedErrorMessage:
        """Format an error message with full context."""
        
        template = self.templates.get(template_key)
        if not template:
            return self._get_fallback_message(context, **format_kwargs)
        
        # Apply localization if available
        localized_template = self.localizer.localize_template(
            template, 
            user_context.locale
        )
        
        # Format with context
        formatted = self._format_template_with_context(
            localized_template,
            context,
            user_context,
            **format_kwargs
        )
        
        # Apply user-specific customizations
        customized = self._apply_user_customizations(
            formatted,
            user_context
        )
        
        return customized
    
    def _format_template_with_context(
        self,
        template: ErrorMessageTemplate,
        context: ErrorContext,
        user_context: UserContext,
        **format_kwargs
    ) -> FormattedErrorMessage:
        """Format template with comprehensive context."""
        
        # Build formatting context
        format_context = {
            # User context
            'user_name': user_context.display_name,
            'user_mention': user_context.mention,
            'prefix': context.command_prefix,
            
            # Command context
            'command_name': context.command_name,
            'command_usage': self._get_command_usage(context.command_name),
            
            # Server context
            'guild_name': context.guild_name,
            'channel_name': context.channel_name,
            
            # Error-specific context
            **format_kwargs
        }
        
        # Format each component
        formatted_title = template.title.format(**format_context)
        formatted_description = template.description.format(**format_context)
        formatted_reason = template.reason.format(**format_context) if template.reason else None
        formatted_solution = template.solution.format(**format_context) if template.solution else None
        
        return FormattedErrorMessage(
            title=formatted_title,
            description=formatted_description,
            reason=formatted_reason,
            solution=formatted_solution,
            help_command=template.help_command,
            severity=template.severity,
            category=template.category,
            include_sentry_id=template.include_sentry_id,
            ephemeral=template.ephemeral
        )
```

### Progressive Disclosure System

```python
class ProgressiveErrorDisclosure:
    """Implements progressive disclosure for error messages."""
    
    def create_progressive_error_embed(
        self,
        formatted_message: FormattedErrorMessage,
        detail_level: DetailLevel = DetailLevel.BASIC
    ) -> discord.Embed:
        """Create error embed with progressive disclosure."""
        
        embed = discord.Embed(
            title=f"❌ {formatted_message.title}",
            description=formatted_message.description,
            color=self._get_severity_color(formatted_message.severity)
        )
        
        # Always include basic information
        if formatted_message.reason and detail_level >= DetailLevel.BASIC:
            embed.add_field(
                name="Why did this happen?",
                value=formatted_message.reason,
                inline=False
            )
        
        # Include solution for basic and above
        if formatted_message.solution and detail_level >= DetailLevel.BASIC:
            embed.add_field(
                name="💡 How to fix this",
                value=formatted_message.solution,
                inline=False
            )
        
        # Include help command for detailed level
        if formatted_message.help_command and detail_level >= DetailLevel.DETAILED:
            embed.add_field(
                name="📚 Get more help",
                value=f"Use `{formatted_message.help_command}` for more information",
                inline=False
            )
        
        # Include technical details for debug level
        if detail_level >= DetailLevel.DEBUG:
            self._add_debug_information(embed, formatted_message)
        
        # Add footer and timestamp
        embed.set_footer(text="Need more help? Contact support or use the help command")
        embed.timestamp = discord.utils.utcnow()
        
        return embed
    
    def create_expandable_error_view(
        self,
        formatted_message: FormattedErrorMessage
    ) -> discord.ui.View:
        """Create an expandable view for error details."""
        
        return ErrorDetailView(formatted_message)

class ErrorDetailView(discord.ui.View):
    """Interactive view for expanding error details."""
    
    def __init__(self, formatted_message: FormattedErrorMessage):
        super().__init__(timeout=300)
        self.formatted_message = formatted_message
        self.current_detail_level = DetailLevel.BASIC
    
    @discord.ui.button(label="Show More Details", style=discord.ButtonStyle.secondary, emoji="🔍")
    async def show_details(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show more error details."""
        
        if self.current_detail_level == DetailLevel.BASIC:
            self.current_detail_level = DetailLevel.DETAILED
            button.label = "Show Debug Info"
        elif self.current_detail_level == DetailLevel.DETAILED:
            self.current_detail_level = DetailLevel.DEBUG
            button.label = "Hide Details"
            button.style = discord.ButtonStyle.danger
        else:
            self.current_detail_level = DetailLevel.BASIC
            button.label = "Show More Details"
            button.style = discord.ButtonStyle.secondary
        
        # Update embed with new detail level
        disclosure = ProgressiveErrorDisclosure()
        updated_embed = disclosure.create_progressive_error_embed(
            self.formatted_message,
            self.current_detail_level
        )
        
        await interaction.response.edit_message(embed=updated_embed, view=self)
    
    @discord.ui.button(label="Get Help", style=discord.ButtonStyle.primary, emoji="❓")
    async def get_help(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show help for resolving the error."""
        
        if self.formatted_message.help_command:
            help_embed = discord.Embed(
                title="Getting Help",
                description=f"Use `{self.formatted_message.help_command}` for detailed information about this command.",
                color=discord.Color.blue()
            )
        else:
            help_embed = discord.Embed(
                title="Getting Help",
                description="Contact a server administrator or bot support for assistance with this error.",
                color=discord.Color.blue()
            )
        
        await interaction.response.send_message(embed=help_embed, ephemeral=True)
```

## Localization Support

### Message Localization System

```python
class MessageLocalizer:
    """Handles localization of error messages."""
    
    def __init__(self):
        self.translations = self._load_translations()
        self.default_locale = "en-US"
    
    def localize_template(
        self,
        template: ErrorMessageTemplate,
        locale: str | None = None
    ) -> ErrorMessageTemplate:
        """Localize an error message template."""
        
        if not locale or locale == self.default_locale:
            return template
        
        locale_key = template.locale_key or self._generate_locale_key(template)
        translations = self.translations.get(locale, {})
        
        if locale_key not in translations:
            return template  # Fallback to default
        
        localized_data = translations[locale_key]
        
        return ErrorMessageTemplate(
            title=localized_data.get('title', template.title),
            description=localized_data.get('description', template.description),
            reason=localized_data.get('reason', template.reason),
            solution=localized_data.get('solution', template.solution),
            help_command=localized_data.get('help_command', template.help_command),
            severity=template.severity,
            category=template.category,
            user_facing=template.user_facing,
            include_sentry_id=template.include_sentry_id,
            ephemeral=template.ephemeral,
            locale_key=locale_key
        )
    
    def _load_translations(self) -> dict[str, dict[str, dict[str, str]]]:
        """Load translation files."""
        # Implementation would load from JSON/YAML files
        return {
            "es-ES": {
                "PERMISSION_DENIED": {
                    "title": "Permiso Requerido",
                    "description": "No tienes permiso para usar este comando.",
                    "reason": "Este comando requiere el nivel de permiso `{permission}`.",
                    "solution": "Contacta a un administrador del servidor si crees que deberías tener acceso."
                }
            },
            "fr-FR": {
                "PERMISSION_DENIED": {
                    "title": "Permission Requise",
                    "description": "Vous n'avez pas la permission d'utiliser cette commande.",
                    "reason": "Cette commande nécessite le niveau de permission `{permission}`.",
                    "solution": "Contactez un administrateur du serveur si vous pensez que vous devriez avoir accès."
                }
            }
        }
```

## Smart Error Recovery

### Recovery Suggestion System

```python
class ErrorRecoverySystem:
    """Provides smart recovery suggestions for errors."""
    
    def __init__(self, bot: Tux):
        self.bot = bot
        self.recovery_strategies = self._build_recovery_strategies()
    
    def get_recovery_suggestions(
        self,
        error: Exception,
        context: ErrorContext
    ) -> list[RecoverySuggestion]:
        """Get contextual recovery suggestions for an error."""
        
        error_type = type(error).__name__
        suggestions = []
        
        # Get base suggestions for error type
        if error_type in self.recovery_strategies:
            base_suggestions = self.recovery_strategies[error_type]
            suggestions.extend(base_suggestions)
        
        # Add context-specific suggestions
        context_suggestions = self._get_context_suggestions(error, context)
        suggestions.extend(context_suggestions)
        
        # Add smart suggestions based on user history
        smart_suggestions = self._get_smart_suggestions(error, context)
        suggestions.extend(smart_suggestions)
        
        return suggestions[:3]  # Limit to top 3 suggestions
    
    def _get_context_suggestions(
        self,
        error: Exception,
        context: ErrorContext
    ) -> list[RecoverySuggestion]:
        """Get suggestions based on current context."""
        
        suggestions = []
        
        # Command-specific suggestions
        if context.command_name:
            if similar_commands := self._find_similar_commands(context.command_name):
                suggestions.append(RecoverySuggestion(
                    title="Did you mean?",
                    description=f"Try `{similar_commands[0]}` instead",
                    action_type=ActionType.COMMAND_SUGGESTION,
                    action_data={"command": similar_commands[0]}
                ))
        
        # Permission-based suggestions
        if isinstance(error, (PermissionLevelError, AppCommandPermissionLevelError)):
            suggestions.append(RecoverySuggestion(
                title="Check your permissions",
                description="Use `/permissions` to see your current permission level",
                action_type=ActionType.COMMAND_SUGGESTION,
                action_data={"command": "permissions"}
            ))
        
        return suggestions
    
    def _get_smart_suggestions(
        self,
        error: Exception,
        context: ErrorContext
    ) -> list[RecoverySuggestion]:
        """Get AI-powered smart suggestions."""
        
        # This could integrate with an AI service for contextual suggestions
        # For now, implement rule-based smart suggestions
        
        suggestions = []
        
        # Analyze user's recent command history
        recent_commands = self._get_recent_user_commands(context.user_id)
        
        # Suggest based on patterns
        if self._is_repeated_error(error, context.user_id):
            suggestions.append(RecoverySuggestion(
                title="Repeated error detected",
                description="This error has occurred multiple times. Consider checking the help documentation.",
                action_type=ActionType.HELP_SUGGESTION,
                action_data={"help_topic": context.command_name}
            ))
        
        return suggestions

@dataclass
class RecoverySuggestion:
    """Represents a recovery suggestion for an error."""
    
    title: str
    description: str
    action_type: ActionType
    action_data: dict[str, Any]
    priority: int = 1  # Higher = more important
```

## Implementation Strategy

### Phase 1: Template System (Week 1-2)

- [ ] Create `ErrorMessageTemplate` class
- [ ] Define template categories and base templates
- [ ] Implement `ErrorMessageFormatter`
- [ ] Update existing error handlers to use templates

### Phase 2: Progressive Disclosure (Week 3-4)

- [ ] Implement `ProgressiveErrorDisclosure`
- [ ] Create `ErrorDetailView` for interactive details
- [ ] Add detail level controls
- [ ] Test user experience with different detail levels

### Phase 3: Localization Support (Week 5-6)

- [ ] Implement `MessageLocalizer`
- [ ] Create translation files for common languages
- [ ] Add locale detection for users
- [ ] Test localized error messages

### Phase 4: Smart Recovery (Week 7-8)

- [ ] Implement `ErrorRecoverySystem`
- [ ] Add context-aware suggestions
- [ ] Create recovery action handlers
- [ ] Test recovery suggestion accuracy

### Phase 5: Integration and Testing (Week 9-10)

- [ ] Integrate all components with existing error handler
- [ ] Comprehensive testing of all error scenarios
- [ ] User experience testing and feedback
- [ ] Performance optimization and monitoring

## Success Metrics

### User Experience

- **Message Clarity**: 90% of users understand error messages without additional help
- **Recovery Success**: 70% of users successfully resolve errors using provided guidance
- **Support Reduction**: 50% reduction in support requests for common errors

### System Performance

- **Response Time**: Error message generation under 100ms
- **Localization Coverage**: Support for top 5 languages used by bot users
- **Template Coverage**: 95% of errors use standardized templates

### Developer Experience

- **Template Reuse**: 80% reduction in duplicate error message code
- **Maintenance Efficiency**: Faster error message updates and improvements
- **Consistency**: All error messages follow standardized format and tone

This comprehensive user-friendly error message system will significantly improve the user experience while maintaining technical accuracy and providing developers with powerful tools for error communication.
