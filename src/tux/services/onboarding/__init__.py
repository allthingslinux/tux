"""Onboarding service package for Tux Discord bot.

This package provides comprehensive guild onboarding functionality including:
- Automated permission rank initialization
- Dedicated onboarding channels
- Interactive setup wizards
- Feature gating based on completion status
"""

from .service import GuildOnboardingService

__all__ = [
    "GuildOnboardingService",
]
