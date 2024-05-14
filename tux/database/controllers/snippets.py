import datetime

from prisma.models import Snippets
from tux.database.client import db


class SnippetsController:
    def __init__(self) -> None:
        """
        Initializes the controller and connects to the snippets table in the database.
        """
        self.table = db.snippets

    async def get_all_snippets(self) -> list[Snippets]:
        """
        Retrieves all snippets from the database.

        Returns
        -------
        list[Snippets]
            A list of all snippets.
        """
        return await self.table.find_many()

    async def get_all_snippets_sorted(self, newestfirst: bool = True) -> list[Snippets]:
        """
        Retrieves all snippets from the database sorted by creation date.

        Parameters
        ----------
        newestfirst : bool, optional
            Whether to sort the snippets by newest first or oldest first, by default True.

        Returns
        -------
        list[Snippets]
            A list of all snippets sorted by creation date.
        """
        return await self.table.find_many(order={"created_at": "desc" if newestfirst else "asc"})

    async def get_snippet_by_name(self, name: str) -> Snippets | None:
        """
        Retrieves a snippet from the database based on the specified name.

        Parameters
        ----------
        name : str
            The name of the snippet to retrieve.

        Returns
        -------
        Snippets or None
            The snippet if found, otherwise None.
        """
        return await self.table.find_first(where={"name": name})

    async def get_snippet_by_name_in_server(self, name: str, server_id: int) -> Snippets | None:
        """
        Retrieves a snippet from the database based on the specified name and server ID.

        Parameters
        ----------
        name : str
            The name of the snippet to retrieve.
        server_id : int
            The server ID to retrieve the snippet from.

        Returns
        -------
        Snippets or None
            The snippet if found, otherwise None.
        """
        return await self.table.find_first(where={"name": name, "server_id": server_id})

    async def create_snippet(
        self, name: str, content: str, created_at: datetime.datetime, author_id: int, server_id: int
    ) -> Snippets:
        """
        Creates a new snippet in the database with the specified name, content, creation date, and author ID.

        Parameters
        ----------
        name : str
            The name of the snippet.
        content : str
            The content of the snippet.
        created_at : datetime.datetime
            The creation date of the snippet.
        author_id : int
            The ID of the author who created the snippet.

        Returns
        -------
        Snippets
            The newly created snippet.
        """
        return await self.table.create(
            data={
                "name": name,
                "content": content,
                "created_at": created_at,
                "author_id": author_id,
                "server_id": server_id,
            }
        )

    async def delete_snippet(self, name: str) -> None:
        """
        Deletes a snippet from the database based on the specified name.

        Parameters
        ----------
        name : str
            The name of the snippet to delete.

        Returns
        -------
        None
        """
        await self.table.delete(where={"name": name})

    async def update_snippet(
        self, name: str, content: str, server_id: int | None
    ) -> Snippets | None:
        """
        Updates a snippet in the database with the specified name and new content.

        Parameters
        ----------
        name : str
            The name of the snippet to update.
        content : str
            The new content for the snippet.
        server_id : int, optional
            The server ID to update the snippet with, by default None.

        Returns
        -------
        Snippets or None
            The updated snippet if successful, otherwise None if the snippet was not found.
        """

        if server_id:
            return await self.table.update(
                where={"name": name},
                data={"content": content, "server_id": server_id},
            )

        return await self.table.update(
            where={"name": name},
            data={"content": content},
        )
