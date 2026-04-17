"""Code execution (e.g. run/eval wrappers) exceptions."""

from .base import TuxError

__all__ = [
    "TuxCodeExecutionError",
    "TuxCompilationError",
    "TuxInvalidCodeFormatError",
    "TuxMissingCodeError",
    "TuxUnsupportedLanguageError",
]


class TuxCodeExecutionError(TuxError):
    """Base exception for code execution errors."""


class TuxMissingCodeError(TuxCodeExecutionError):
    """Raised when no code is provided for execution."""

    def __init__(self) -> None:
        super().__init__(
            "Please provide code with syntax highlighting in this format:\n"
            '```\n`\u200b``python\nprint("Hello, World!")\n`\u200b``\n```',
        )


class TuxInvalidCodeFormatError(TuxCodeExecutionError):
    """Raised when code format is invalid."""

    def __init__(self) -> None:
        super().__init__(
            "Please provide code with syntax highlighting in this format:\n"
            '```\n`\u200b``python\nprint("Hello, World!")\n`\u200b``\n```',
        )


class TuxUnsupportedLanguageError(TuxCodeExecutionError):
    """Raised when the specified language is not supported."""

    def __init__(self, language: str, supported_languages: list[str]) -> None:
        self.language = language
        self.supported_languages = supported_languages
        available_langs = ", ".join(supported_languages)

        # Sanitize language input to prevent formatting issues in error messages
        # Extract first word (language name) and truncate to prevent malicious/long inputs
        language_str = language.strip()
        # Get first word only (language names are typically single words)
        first_word = language_str.split()[0] if language_str.split() else language_str
        # Truncate to max 30 characters to prevent extremely long inputs
        sanitized_language = first_word[:30] if len(first_word) > 30 else first_word

        super().__init__(
            f"No compiler found for `{sanitized_language}`. The following languages are supported:\n```{available_langs}```",
        )


class TuxCompilationError(TuxCodeExecutionError):
    """Raised when code compilation fails."""

    def __init__(self) -> None:
        super().__init__(
            "Failed to get output from the compiler. The code may have compilation errors.",
        )
