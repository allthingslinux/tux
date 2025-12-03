"""
xkcd Comics API Wrapper for Tux Bot.

This module provides integration with the xkcd webcomic API,
allowing the bot to fetch and display xkcd comics with full metadata
and image processing capabilities.
"""

import datetime
import json
import random
from io import BytesIO
from typing import Any

import httpx
from PIL import Image, UnidentifiedImageError

from tux.shared.exceptions import (
    TuxAPIConnectionError,
    TuxAPIRequestError,
    TuxAPIResourceNotFoundError,
)


class HttpError(Exception):
    """Exception raised for HTTP-related errors in xkcd API calls."""

    def __init__(self, status_code: int, reason: str) -> None:
        """
        Initialize the HttpError.

        Parameters
        ----------
        status_code : int
            The status code of the error.
        reason : str
            The reason of the error.
        """
        self.status_code = status_code
        self.reason = reason
        super().__init__(f"HTTP Error {status_code}: {reason}")


class Comic:
    """A class representing an xkcd comic."""

    def __init__(
        self,
        xkcd_dict: dict[str, Any],
        raw_image: bytes | None = None,
        comic_url: str | None = None,
        explanation_url: str | None = None,
    ) -> None:
        """Initialize a Comic instance from xkcd API data.

        Parameters
        ----------
        xkcd_dict : dict[str, Any]
            Dictionary containing xkcd comic metadata from the API.
        raw_image : bytes, optional
            Raw image data for the comic.
        comic_url : str, optional
            Direct URL to the comic page.
        explanation_url : str, optional
            URL to the comic explanation.
        """
        self.id: int | None = xkcd_dict.get("num")
        self.date: datetime.date | None = self._determine_date(xkcd_dict)
        self.title: str | None = xkcd_dict.get("safe_title")
        self.description: str | None = xkcd_dict.get("alt")
        self.transcript: str | None = xkcd_dict.get("transcript")
        self.image: bytes | None = raw_image
        self.image_extension: str | None = self._determine_image_extension()
        self.image_url: str | None = xkcd_dict.get("img")
        self.comic_url: str | None = comic_url
        self.explanation_url: str | None = explanation_url

    @staticmethod
    def _determine_date(xkcd_dict: dict[str, Any]) -> datetime.date | None:
        """
        Determine the date of the comic.

        Parameters
        ----------
        xkcd_dict : dict[str, Any]
            The dictionary containing the comic data.

        Returns
        -------
        datetime.date | None
            The date of the comic.
        """
        try:
            return datetime.date(
                int(xkcd_dict["year"]),
                int(xkcd_dict["month"]),
                int(xkcd_dict["day"]),
            )

        except (KeyError, ValueError):
            return None

    def _determine_image_extension(self) -> str | None:
        """
        Determine the image extension of the comic.

        Returns
        -------
        str | None
            The extension of the image.
        """
        if self.image:
            try:
                image = Image.open(BytesIO(self.image))
                return f".{image.format.lower()}" if image.format else None
            except (OSError, UnidentifiedImageError):
                return None
        return None

    def update_raw_image(self, raw_image: bytes) -> None:
        """
        Update the raw image of the comic.

        Parameters
        ----------
        raw_image : bytes
            The raw image data.
        """
        self.image = raw_image
        self.image_extension = self._determine_image_extension()

    def __repr__(self) -> str:
        """
        Return the representation of the comic.

        Returns
        -------
        str
            The representation of the comic.
        """
        return f"Comic({self.title})"


class Client:
    """xkcd API client for fetching and managing comics."""

    def __init__(
        self,
        api_url: str = "https://xkcd.com",
        explanation_wiki_url: str = "https://www.explainxkcd.com/wiki/index.php/",
    ) -> None:
        """
        Initialize the Client.

        Parameters
        ----------
        api_url : str, optional
            The URL of the xkcd API, by default "https://xkcd.com"
        explanation_wiki_url : str, optional
            The URL of the xkcd explanation wiki, by default "https://www.explainxkcd.com/wiki/index.php/"
        """
        self._api_url = api_url
        self._explanation_wiki_url = explanation_wiki_url

    def latest_comic_url(self) -> str:
        """
        Get the URL for the latest comic.

        Returns
        -------
        str
            The URL for the latest comic.
        """
        return f"{self._api_url}/info.0.json"

    def comic_id_url(self, comic_id: int) -> str:
        """
        Get the URL for a specific comic ID.

        Parameters
        ----------
        comic_id : int
            The ID of the comic.

        Returns
        -------
        str
            The URL for the specific comic ID.
        """
        return f"{self._api_url}/{comic_id}/info.0.json"

    def _parse_response(self, response_text: str) -> Comic:
        """
        Parse the response text into a Comic object.

        Parameters
        ----------
        response_text : str
            The response text to parse.

        Returns
        -------
        Comic
            The parsed comic object.
        """
        response_dict: dict[str, Any] = json.loads(response_text)
        comic_url: str = f"{self._api_url}/{response_dict['num']}/"
        explanation_url: str = f"{self._explanation_wiki_url}{response_dict['num']}"

        return Comic(
            response_dict,
            comic_url=comic_url,
            explanation_url=explanation_url,
        )

    def _fetch_comic(self, comic_id: int, raw_comic_image: bool) -> Comic:
        """
        Fetch a comic from the xkcd API.

        Parameters
        ----------
        comic_id : int
            The ID of the comic to fetch.
        raw_comic_image : bool
            Whether to fetch the raw image data.

        Returns
        -------
        Comic
            The fetched comic.
        """
        comic = self._parse_response(self._request_comic(comic_id))

        if raw_comic_image:
            raw_image = self._request_raw_image(comic.image_url)
            comic.update_raw_image(raw_image)

        return comic

    def get_latest_comic(self, raw_comic_image: bool = False) -> Comic:
        """
        Get the latest xkcd comic.

        Parameters
        ----------
        raw_comic_image : bool, optional
            Whether to fetch the raw image data, by default False

        Returns
        -------
        Comic
            The latest xkcd comic.
        """
        return self._fetch_comic(0, raw_comic_image)

    def get_comic(self, comic_id: int, raw_comic_image: bool = False) -> Comic:
        """
        Get a specific xkcd comic.

        Parameters
        ----------
        comic_id : int
            The ID of the comic to fetch.
        raw_comic_image : bool, optional
            Whether to fetch the raw image data, by default False

        Returns
        -------
        Comic
            The fetched xkcd comic.
        """
        return self._fetch_comic(comic_id, raw_comic_image)

    def get_random_comic(self, raw_comic_image: bool = False) -> Comic:
        """
        Get a random xkcd comic.

        Parameters
        ----------
        raw_comic_image : bool, optional
            Whether to fetch the raw image data, by default False

        Returns
        -------
        Comic
            The random xkcd comic.
        """
        latest_comic_id: int = self._parse_response(self._request_comic(0)).id or 0
        random_id: int = random.randint(1, latest_comic_id)

        return self._fetch_comic(random_id, raw_comic_image)

    def _request_comic(self, comic_id: int) -> str:
        """
        Request the comic data from the xkcd API.

        Parameters
        ----------
        comic_id : int
            The ID of the comic to fetch.

        Returns
        -------
        str
            The response text.

        Raises
        ------
        TuxAPIConnectionError
            If connection to xkcd API fails.
        TuxAPIRequestError
            If the API request fails.
        TuxAPIResourceNotFoundError
            If the comic is not found.
        """
        comic_url = (
            self.latest_comic_url() if comic_id <= 0 else self.comic_id_url(comic_id)
        )

        try:
            response = httpx.get(comic_url)
            response.raise_for_status()

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise TuxAPIResourceNotFoundError(
                    service_name="xkcd",
                    resource_identifier=str(comic_id),
                ) from exc
            raise TuxAPIRequestError(
                service_name="xkcd",
                status_code=exc.response.status_code,
                reason=exc.response.reason_phrase,
            ) from exc
        except httpx.RequestError as exc:
            raise TuxAPIConnectionError(
                service_name="xkcd",
                original_error=exc,
            ) from exc

        return response.text

    @staticmethod
    def _request_raw_image(raw_image_url: str | None) -> bytes:
        """
        Request the raw image data from the xkcd API.

        Parameters
        ----------
        raw_image_url : str | None
            The URL of the raw image data.

        Returns
        -------
        bytes
            The raw image data.

        Raises
        ------
        TuxAPIConnectionError
            If connection to xkcd API fails.
        TuxAPIRequestError
            If the API request fails.
        TuxAPIResourceNotFoundError
            If the image is not found or URL is not provided.
        """
        if not raw_image_url:
            raise TuxAPIResourceNotFoundError(
                service_name="xkcd",
                resource_identifier="image_url_not_provided",
            )

        try:
            response = httpx.get(raw_image_url)
            response.raise_for_status()

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise TuxAPIResourceNotFoundError(
                    service_name="xkcd",
                    resource_identifier=raw_image_url,
                ) from exc
            raise TuxAPIRequestError(
                service_name="xkcd",
                status_code=exc.response.status_code,
                reason=exc.response.reason_phrase,
            ) from exc
        except httpx.RequestError as exc:
            raise TuxAPIConnectionError(
                service_name="xkcd",
                original_error=exc,
            ) from exc

        return response.content

    def __repr__(self) -> str:
        """
        Return the representation of the client.

        Returns
        -------
        str
            The representation of the client.
        """
        return "Client()"
