import datetime
import imghdr
import json
import random
from typing import Any

import httpx


class HttpError(Exception):
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
    """
    A class representing an xkcd comic.
    """

    def __init__(
        self,
        xkcd_dict: dict[str, Any],
        raw_image: bytes | None = None,
        comic_url: str | None = None,
        explanation_url: str | None = None,
    ) -> None:
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
            return datetime.date(int(xkcd_dict["year"]), int(xkcd_dict["month"]), int(xkcd_dict["day"]))

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
        return f".{imghdr.what(None, h=self.image)}" if self.image else None

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
    def __init__(
        self,
        api_url: str = "https://xkcd.com",
        explanation_wiki_url: str = "https://www.explainxkcd.com/wiki/index.php/",
    ) -> None:
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

        return Comic(response_dict, comic_url=comic_url, explanation_url=explanation_url)

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
        HttpError
            If the request fails.
        """
        comic_url = self.latest_comic_url() if comic_id <= 0 else self.comic_id_url(comic_id)

        try:
            response = httpx.get(comic_url)
            response.raise_for_status()

        except httpx.HTTPStatusError as exc:
            raise HttpError(exc.response.status_code, exc.response.reason_phrase) from exc

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
        HttpError
            If the request fails.
        """
        if not raw_image_url:
            raise HttpError(404, "Image URL not found")

        try:
            response = httpx.get(raw_image_url)
            response.raise_for_status()

        except httpx.HTTPStatusError as exc:
            raise HttpError(exc.response.status_code, exc.response.reason_phrase) from exc

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
