from prisma.models import Snippets
from tux.database.client import db


class SnippetsController:
    def __init__(self) -> None:
        self.table = db.snippets

    async def get_all_snippets(self) -> list[Snippets]:
        """
        Retrieves all snippets from the database.

        Returns:
            list[Snippets]: A list of all snippets.
        """

        return await self.table.find_many()

    async def get_snippet_by_name(self, name: str) -> Snippets | None:
        """
        Retrieves a snippet from the database based on the specified name.

        Args:
            name (str): The name of the snippet to retrieve.

        Returns:
            Snippets | None: The snippet if found, None if the snippet does not exist.
        """

        return await self.table.find_first(where={"name": name})

    async def create_snippet(self, name: str, content: str) -> Snippets:
        """
        Creates a new snippet in the database with the specified name and content.

        Args:
            name (str): The name of the snippet.
            content (str): The content of the snippet.

        Returns:
            Snippets: The newly created snippet.
        """

        return await self.table.create(
            data={
                "name": name,
                "content": content,
            }
        )

    async def delete_snippet(self, name: str) -> None:
        """
        Deletes a snippet from the database based on the specified name.

        Args:
            name (str): The name of the snippet to delete.

        Returns:
            None
        """

        await self.table.delete(where={"name": name})

    async def update_snippet(self, name: str, content: str) -> Snippets | None:
        """
        Updates a snippet in the database with the specified name and content.

        Args:
            name (str): The name of the snippet to update.
            content (str): The new content for the snippet.

        Returns:
            Snippets | None: The updated snippet if successful, None if the snippet was not found.
        """

        return await self.table.update(
            where={"name": name},
            data={"content": content},
        )
