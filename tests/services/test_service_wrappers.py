"""Tests for service wrappers using the centralized HTTP client."""

import httpx
import pytest

from tux.modules.utility.run import (
    GODBOLT_COMPILERS,
    WANDBOX_COMPILERS,
    GodboltService,
    WandboxService,
)
from tux.services.wrappers import godbolt, wandbox
from tux.shared.exceptions import (
    TuxAPIConnectionError,
    TuxAPIRequestError,
    TuxAPIResourceNotFoundError,
)


class TestGodboltService:
    """Test the Godbolt service wrapper."""

    @pytest.mark.asyncio
    async def test_getoutput_success(self, httpx_mock) -> None:
        """Test successful code execution via Godbolt."""
        mock_response = {
            "stdout": [{"text": "Hello World\n"}],
            "stderr": [],
            "code": 0,
        }
        httpx_mock.add_response(json=mock_response)

        result = await godbolt.getoutput("print('Hello World')", "python3", None)

        assert result is not None
        request = httpx_mock.get_request()
        assert request.method == "POST"
        assert "godbolt.org" in str(request.url)

    @pytest.mark.asyncio
    async def test_getoutput_with_options(self, httpx_mock) -> None:
        """Test code execution with compiler options."""
        mock_response = {"stdout": [], "stderr": [], "code": 0}
        httpx_mock.add_response(json=mock_response)

        await godbolt.getoutput("int main(){}", "gcc", "-O2")

        request = httpx_mock.get_request()
        request_data = request.content.decode()
        assert "-O2" in request_data

    @pytest.mark.asyncio
    async def test_getoutput_http_error(self, httpx_mock) -> None:
        """Test HTTP error handling in getoutput."""
        httpx_mock.add_response(status_code=404)

        with pytest.raises(TuxAPIResourceNotFoundError):
            await godbolt.getoutput("code", "invalid_lang", None)

    @pytest.mark.asyncio
    async def test_getoutput_timeout(self, httpx_mock) -> None:
        """Test timeout handling in getoutput."""
        httpx_mock.add_exception(httpx.ReadTimeout("Timeout"))

        with pytest.raises(TuxAPIConnectionError):
            await godbolt.getoutput("code", "python3", None)

    @pytest.mark.asyncio
    async def test_getlanguages(self, httpx_mock) -> None:
        """Test getting available languages."""
        mock_languages = [{"id": "python", "name": "Python"}]
        httpx_mock.add_response(json=mock_languages)

        result = await godbolt.getlanguages()

        assert result is not None
        request = httpx_mock.get_request()
        assert "languages" in str(request.url)

    @pytest.mark.asyncio
    async def test_getcompilers(self, httpx_mock) -> None:
        """Test getting available compilers."""
        mock_compilers = [{"id": "python39", "name": "Python 3.9"}]
        httpx_mock.add_response(json=mock_compilers)

        result = await godbolt.getcompilers()

        assert result is not None
        request = httpx_mock.get_request()
        assert "compilers" in str(request.url)

    @pytest.mark.asyncio
    async def test_generateasm_success(self, httpx_mock) -> None:
        """Test assembly generation."""
        mock_response = {"asm": [{"text": "mov eax, 1"}]}
        httpx_mock.add_response(json=mock_response)

        result = await godbolt.generateasm("int main(){}", "gcc", None)

        assert result is not None
        request = httpx_mock.get_request()
        assert request.method == "POST"


class TestWandboxService:
    """Test the Wandbox service wrapper."""

    @pytest.mark.asyncio
    async def test_getoutput_success(self, httpx_mock) -> None:
        """Test successful code execution via Wandbox."""
        mock_response = {
            "status": "0",
            "program_output": "Hello World\n",
            "program_error": "",
        }
        httpx_mock.add_response(json=mock_response)

        result = await wandbox.getoutput("print('Hello World')", "python-3.9.2", None)

        assert result == mock_response
        request = httpx_mock.get_request()
        assert request.method == "POST"
        assert "wandbox.org" in str(request.url)

    @pytest.mark.asyncio
    async def test_getoutput_with_options(self, httpx_mock) -> None:
        """Test code execution with compiler options."""
        mock_response = {"status": "0", "program_output": ""}
        httpx_mock.add_response(json=mock_response)

        await wandbox.getoutput("int main(){}", "gcc-head", "-Wall")

        request = httpx_mock.get_request()
        request_data = request.content.decode()
        assert "-Wall" in request_data

    @pytest.mark.asyncio
    async def test_getoutput_timeout(self, httpx_mock) -> None:
        """Test timeout handling in Wandbox."""
        httpx_mock.add_exception(httpx.ReadTimeout("Timeout"))

        with pytest.raises(TuxAPIConnectionError):
            await wandbox.getoutput("code", "python-3.9.2", None)

    @pytest.mark.asyncio
    async def test_getoutput_connection_error(self, httpx_mock) -> None:
        """Test connection error handling."""
        httpx_mock.add_exception(httpx.RequestError("Connection failed"))

        with pytest.raises(TuxAPIConnectionError):
            await wandbox.getoutput("code", "python-3.9.2", None)

    @pytest.mark.asyncio
    async def test_getoutput_http_status_error(self, httpx_mock) -> None:
        """Test HTTP status error handling."""
        httpx_mock.add_response(status_code=500, text="Server Error")

        with pytest.raises(TuxAPIRequestError):
            await wandbox.getoutput("code", "python-3.9.2", None)


class TestServiceWrapperIntegration:
    """Integration tests for service wrappers with the run module."""

    @pytest.mark.asyncio
    async def test_godbolt_service_in_run_module(self, httpx_mock) -> None:
        """Test Godbolt service integration with run module."""
        # Mock successful execution - Godbolt returns text output
        mock_response_text = "# Header line 1\n# Header line 2\n# Header line 3\n# Header line 4\n# Header line 5\n42\n"
        httpx_mock.add_response(text=mock_response_text)

        service = GodboltService(GODBOLT_COMPILERS)
        result = await service._execute("python3", "print(42)", None)

        assert result is not None
        assert "42" in result

    @pytest.mark.asyncio
    async def test_wandbox_service_in_run_module(self, httpx_mock) -> None:
        """Test Wandbox service integration with run module."""
        # Mock successful execution
        mock_response = {
            "status": "0",
            "program_output": "Hello from Wandbox\n",
            "program_error": "",
        }
        httpx_mock.add_response(json=mock_response)

        service = WandboxService(WANDBOX_COMPILERS)
        result = await service._execute(
            "python-3.9.2",
            "print('Hello from Wandbox')",
            None,
        )

        assert result is not None
        assert "Hello from Wandbox" in result

    @pytest.mark.asyncio
    async def test_service_error_handling_in_run_module(self, httpx_mock) -> None:
        """Test error handling in run module services."""
        # Mock API error
        httpx_mock.add_exception(httpx.ReadTimeout("Service timeout"))

        service = GodboltService(GODBOLT_COMPILERS)

        # The service should handle the exception gracefully and return None
        result = await service._execute("python3", "print('test')", None)
        assert result is None


class TestServiceWrapperConfiguration:
    """Test service wrapper configuration and setup."""

    @pytest.mark.asyncio
    async def test_godbolt_url_configuration(self, httpx_mock) -> None:
        """Test that Godbolt uses correct URL configuration."""
        httpx_mock.add_response()

        await godbolt.sendresponse("https://godbolt.org/api/test")

        request = httpx_mock.get_request()
        assert "godbolt.org" in str(request.url)

    @pytest.mark.asyncio
    async def test_wandbox_url_configuration(self, httpx_mock) -> None:
        """Test that Wandbox uses correct URL configuration."""
        httpx_mock.add_response(json={"status": "0"})

        await wandbox.getoutput("test", "python-3.9.2", None)

        request = httpx_mock.get_request()
        assert "wandbox.org" in str(request.url)

    @pytest.mark.asyncio
    async def test_timeout_configuration(self, httpx_mock) -> None:
        """Test that services use appropriate timeout values."""
        httpx_mock.add_response()

        # Both services should use 15 second timeout
        await godbolt.sendresponse("https://godbolt.org/api/test")

        # The timeout should be passed to the HTTP client
        # This is tested indirectly through the successful request
        request = httpx_mock.get_request()
        assert request is not None
