"""Tests for UI components."""

import pytest
from unittest.mock import Mock

def test_ui_imports():
    """Test that UI components can be imported successfully."""
    # Test main UI module imports
    from tux.ui import EmbedCreator, EmbedType, GithubButton, XkcdButtons

    # Test views imports
    from tux.ui.views import (
        BaseConfirmationView,
        ConfirmationDanger,
        ConfirmationNormal,
        ConfigSetChannels,
        ConfigSetPrivateLogs,
        ConfigSetPublicLogs,
        TldrPaginatorView,
    )

    # Test modals imports
    from tux.ui.modals import ReportModal

    # Test help components
    from tux.ui.help_components import (
        BaseHelpView,
        CategorySelectMenu,
        CommandSelectMenu,
        BackButton,
        CloseButton,
        HelpView,
    )

    # Verify classes exist
    assert EmbedCreator is not None
    assert EmbedType is not None
    assert GithubButton is not None
    assert XkcdButtons is not None
    assert BaseConfirmationView is not None
    assert ReportModal is not None


def test_embed_type_enum():
    """Test that EmbedType enum has all expected values."""
    from tux.ui.embeds import EmbedType

    # Test enum values exist
    assert hasattr(EmbedType, 'DEFAULT')
    assert hasattr(EmbedType, 'INFO')
    assert hasattr(EmbedType, 'ERROR')
    assert hasattr(EmbedType, 'WARNING')
    assert hasattr(EmbedType, 'SUCCESS')
    assert hasattr(EmbedType, 'POLL')
    assert hasattr(EmbedType, 'CASE')
    assert hasattr(EmbedType, 'NOTE')


def test_embed_creator_constants():
    """Test that EmbedCreator has the expected constants."""
    from tux.ui.embeds import EmbedCreator, EmbedType

    # Test that constants match enum values
    assert EmbedCreator.DEFAULT == EmbedType.DEFAULT
    assert EmbedCreator.INFO == EmbedType.INFO
    assert EmbedCreator.ERROR == EmbedType.ERROR
    assert EmbedCreator.WARNING == EmbedType.WARNING
    assert EmbedCreator.SUCCESS == EmbedType.SUCCESS
    assert EmbedCreator.POLL == EmbedType.POLL
    assert EmbedCreator.CASE == EmbedType.CASE
    assert EmbedCreator.NOTE == EmbedType.NOTE


def test_confirmation_view_initialization():
    """Test that confirmation views can be initialized."""
    from tux.ui.views.confirmation import ConfirmationDanger, ConfirmationNormal

    # Test initialization with user ID
    user_id = 12345
    danger_view = ConfirmationDanger(user_id)
    normal_view = ConfirmationNormal(user_id)

    assert danger_view.user == user_id
    assert normal_view.user == user_id
    assert danger_view.value is None
    assert normal_view.value is None
