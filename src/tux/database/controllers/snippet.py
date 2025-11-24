"""
Code snippet storage and management controller.

This controller manages reusable code snippets for Discord guilds, allowing
users to save and retrieve frequently used code blocks and text templates.
"""

from __future__ import annotations

from typing import Any

from tux.database.controllers.base import BaseController
from tux.database.models import Snippet
from tux.database.service import DatabaseService


class SnippetController(BaseController[Snippet]):
    """Clean Snippet controller using the new BaseController pattern."""

    def __init__(self, db: DatabaseService | None = None) -> None:
        """Initialize the snippet controller.

        Parameters
        ----------
        db : DatabaseService | None, optional
            The database service instance. If None, uses the default service.
        """
        super().__init__(Snippet, db)

    # Simple, clean methods that use BaseController's CRUD operations
    async def get_snippet_by_id(self, snippet_id: int) -> Snippet | None:
        """
        Get a snippet by its ID.

        Returns
        -------
        Snippet | None
            The snippet if found, None otherwise.
        """
        return await self.get_by_id(snippet_id)

    async def get_snippet_by_name_and_guild(
        self,
        snippet_name: str,
        guild_id: int,
    ) -> Snippet | None:
        """
        Get a snippet by name and guild.

        Returns
        -------
        Snippet | None
            The snippet if found, None otherwise.
        """
        return await self.find_one(
            filters=(Snippet.snippet_name == snippet_name)
            & (Snippet.guild_id == guild_id),
        )

    async def get_snippets_by_guild(self, guild_id: int) -> list[Snippet]:
        """
        Get all snippets in a guild.

        Returns
        -------
        list[Snippet]
            List of all snippets for the guild.
        """
        return await self.find_all(filters=Snippet.guild_id == guild_id)

    async def create_snippet(
        self,
        snippet_name: str,
        snippet_content: str,
        guild_id: int,
        snippet_user_id: int,
        alias: str | None = None,
        **kwargs: Any,
    ) -> Snippet:
        """
        Create a new snippet.

        Returns
        -------
        Snippet
            The newly created snippet.
        """
        return await self.create(
            snippet_name=snippet_name,
            snippet_content=snippet_content,
            guild_id=guild_id,
            snippet_user_id=snippet_user_id,
            alias=alias,
            uses=0,
            locked=False,
            **kwargs,
        )

    async def update_snippet(self, snippet_id: int, **kwargs: Any) -> Snippet | None:
        """
        Update a snippet by ID.

        Returns
        -------
        Snippet | None
            The updated snippet, or None if not found.
        """
        return await self.update_by_id(snippet_id, **kwargs)

    async def update_snippet_by_id(
        self,
        snippet_id: int,
        **kwargs: Any,
    ) -> Snippet | None:
        """
        Update a snippet by ID - alias for update_snippet.

        Returns
        -------
        Snippet | None
            The updated snippet, or None if not found.
        """
        return await self.update_snippet(snippet_id, **kwargs)

    async def delete_snippet(self, snippet_id: int) -> bool:
        """
        Delete a snippet by ID.

        Returns
        -------
        bool
            True if deleted successfully, False otherwise.
        """
        return await self.delete_by_id(snippet_id)

    async def delete_snippet_by_id(self, snippet_id: int) -> bool:
        """
        Delete a snippet by ID - alias for delete_snippet.

        Returns
        -------
        bool
            True if deleted successfully, False otherwise.
        """
        return await self.delete_snippet(snippet_id)

    async def get_snippets_by_creator(
        self,
        creator_id: int,
        guild_id: int,
    ) -> list[Snippet]:
        """
        Get all snippets created by a specific user in a guild.

        Returns
        -------
        list[Snippet]
            List of snippets created by the user.
        """
        return await self.find_all(
            filters=(Snippet.snippet_user_id == creator_id)
            & (Snippet.guild_id == guild_id),
        )

    async def search_snippets(self, guild_id: int, search_term: str) -> list[Snippet]:
        """
        Search snippets by name or content in a guild.

        Returns
        -------
        list[Snippet]
            List of snippets matching the search term.
        """
        # This is a simple search - in production you might want to use with_session
        # for more complex SQL queries with ILIKE or full-text search
        all_snippets = await self.get_snippets_by_guild(guild_id)
        search_lower = search_term.lower()
        return [
            snippet
            for snippet in all_snippets
            if (
                search_lower in snippet.snippet_name.lower()
                or (
                    snippet.snippet_content
                    and search_lower in snippet.snippet_content.lower()
                )
            )
        ]

    async def get_snippet_count_by_guild(self, guild_id: int) -> int:
        """
        Get the total number of snippets in a guild.

        Returns
        -------
        int
            The total count of snippets in the guild.
        """
        return await self.count(filters=Snippet.guild_id == guild_id)

    # Additional methods that module files expect
    async def find_many(self, **filters: Any) -> list[Snippet]:
        """
        Find many snippets with optional filters - alias for find_all.

        Returns
        -------
        list[Snippet]
            List of snippets matching the filters.
        """
        return await self.find_all()

    async def get_snippet_by_name_and_guild_id(
        self,
        name: str,
        guild_id: int,
    ) -> Snippet | None:
        """
        Get a snippet by name and guild ID.

        Returns
        -------
        Snippet | None
            The snippet if found, None otherwise.
        """
        return await self.find_one(
            filters=(Snippet.snippet_name == name) & (Snippet.guild_id == guild_id),
        )

    async def create_snippet_alias(
        self,
        original_name: str,
        alias_name: str,
        guild_id: int,
    ) -> Snippet:
        """
        Create a snippet alias.

        Returns
        -------
        Snippet
            The newly created alias snippet.

        Raises
        ------
        ValueError
            If the original snippet is not found.
        """
        # Get the original snippet
        original = await self.get_snippet_by_name_and_guild_id(original_name, guild_id)
        if not original:
            error_msg = f"Snippet '{original_name}' not found in guild {guild_id}"
            raise ValueError(error_msg)

        # Create alias with same content but different name
        return await self.create(
            snippet_name=alias_name,
            snippet_content=original.snippet_content,
            snippet_user_id=original.snippet_user_id,
            guild_id=guild_id,
            uses=0,
            locked=original.locked,
            alias=original_name,  # Reference to original
        )

    async def get_snippet_count_by_creator(self, creator_id: int, guild_id: int) -> int:
        """
        Get the number of snippets created by a user in a guild.

        Returns
        -------
        int
            The count of snippets created by the user.
        """
        return await self.count(
            filters=(Snippet.snippet_user_id == creator_id)
            & (Snippet.guild_id == guild_id),
        )

    async def toggle_snippet_lock(self, snippet_id: int) -> Snippet | None:
        """
        Toggle the locked status of a snippet.

        Returns
        -------
        Snippet | None
            The updated snippet, or None if not found.
        """
        snippet = await self.get_snippet_by_id(snippet_id)
        if snippet is None:
            return None
        return await self.update_by_id(snippet_id, locked=not snippet.locked)

    async def toggle_snippet_lock_by_id(self, snippet_id: int) -> Snippet | None:
        """
        Toggle the locked status of a snippet by ID - alias for toggle_snippet_lock.

        Returns
        -------
        Snippet | None
            The updated snippet, or None if not found.
        """
        return await self.toggle_snippet_lock(snippet_id)

    async def increment_snippet_uses(self, snippet_id: int) -> Snippet | None:
        """
        Increment the usage count of a snippet.

        Returns
        -------
        Snippet | None
            The updated snippet, or None if not found.
        """
        snippet = await self.get_snippet_by_id(snippet_id)
        if snippet is None:
            return None
        return await self.update_by_id(snippet_id, uses=snippet.uses + 1)

    async def get_popular_snippets(
        self,
        guild_id: int,
        limit: int = 10,
    ) -> list[Snippet]:
        """
        Get the most popular snippets in a guild by usage count.

        Returns
        -------
        list[Snippet]
            List of snippets sorted by usage count (most popular first).
        """
        # Get all snippets and sort in Python for now to avoid SQLAlchemy ordering type issues
        all_snippets = await self.find_all(filters=Snippet.guild_id == guild_id)
        # Sort by uses descending and limit
        sorted_snippets = sorted(all_snippets, key=lambda x: x.uses, reverse=True)
        return sorted_snippets[:limit]

    async def get_snippets_by_alias(self, alias: str, guild_id: int) -> list[Snippet]:
        """
        Get snippets by alias in a guild.

        Returns
        -------
        list[Snippet]
            List of snippets with the specified alias.
        """
        return await self.find_all(
            filters=(Snippet.alias == alias) & (Snippet.guild_id == guild_id),
        )

    async def get_all_aliases(self, guild_id: int) -> list[Snippet]:
        """
        Get all aliases in a guild.

        Returns
        -------
        list[Snippet]
            List of all alias snippets.
        """
        return await self.find_all(
            filters=(Snippet.alias is not None) & (Snippet.guild_id == guild_id),
        )

    async def get_all_snippets_by_guild_id(self, guild_id: int) -> list[Snippet]:
        """
        Get all snippets in a guild - alias for get_snippets_by_guild.

        Returns
        -------
        list[Snippet]
            List of all snippets for the guild.
        """
        return await self.get_snippets_by_guild(guild_id)
