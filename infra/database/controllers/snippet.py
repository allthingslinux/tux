import datetime

from database.client import db
from database.controllers.base import BaseController

from prisma.actions import GuildActions
from prisma.models import Guild, Snippet


class SnippetController(BaseController[Snippet]):
    """Controller for managing snippets.

    This controller provides methods for managing snippet records in the database.
    It inherits common CRUD operations from BaseController.
    """

    def __init__(self) -> None:
        """Initialize the SnippetController with the snippet table."""
        super().__init__("snippet")
        self.guild_table: GuildActions[Guild] = db.client.guild

    async def get_all_snippets(self) -> list[Snippet]:
        """Get all snippets.

        Returns
        -------
        list[Snippet]
            List of all snippets
        """
        return await self.find_many(where={})

    async def get_all_snippets_by_guild_id(self, guild_id: int, include_guild: bool = False) -> list[Snippet]:
        """Get all snippets for a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to get snippets for
        include_guild : bool
            Whether to include the guild relation

        Returns
        -------
        list[Snippet]
            List of snippets for the guild
        """
        include = {"guild": True} if include_guild else None
        return await self.find_many(where={"guild_id": guild_id}, include=include)

    async def get_all_snippets_sorted(self, newestfirst: bool = True, limit: int | None = None) -> list[Snippet]:
        """Get all snippets sorted by creation time.

        Parameters
        ----------
        newestfirst : bool
            Whether to sort with newest first
        limit : int | None
            Optional maximum number of snippets to return

        Returns
        -------
        list[Snippet]
            List of sorted snippets
        """
        return await self.find_many(
            where={},
            order={"snippet_created_at": "desc" if newestfirst else "asc"},
            take=limit,
        )

    async def get_snippet_by_name(self, snippet_name: str, include_guild: bool = False) -> Snippet | None:
        """Get a snippet by name.

        Parameters
        ----------
        snippet_name : str
            The name of the snippet to get
        include_guild : bool
            Whether to include the guild relation

        Returns
        -------
        Snippet | None
            The snippet if found, None otherwise
        """
        include = {"guild": True} if include_guild else None
        return await self.find_one(
            where={"snippet_name": {"contains": snippet_name, "mode": "insensitive"}},
            include=include,
        )

    async def get_snippet_by_name_and_guild_id(
        self,
        snippet_name: str,
        guild_id: int,
        include_guild: bool = False,
    ) -> Snippet | None:
        """Get a snippet by name and guild ID.

        Parameters
        ----------
        snippet_name : str
            The name of the snippet to get
        guild_id : int
            The ID of the guild to get the snippet from
        include_guild : bool
            Whether to include the guild relation

        Returns
        -------
        Snippet | None
            The snippet if found, None otherwise
        """
        include = {"guild": True} if include_guild else None
        return await self.find_one(
            where={"snippet_name": {"equals": snippet_name, "mode": "insensitive"}, "guild_id": guild_id},
            include=include,
        )

    async def create_snippet(
        self,
        snippet_name: str,
        snippet_content: str,
        snippet_created_at: datetime.datetime,
        snippet_user_id: int,
        guild_id: int,
    ) -> Snippet:
        """Create a new snippet.

        Parameters
        ----------
        snippet_name : str
            The name of the snippet
        snippet_content : str
            The content of the snippet
        snippet_created_at : datetime.datetime
            The creation time of the snippet
        snippet_user_id : int
            The ID of the user creating the snippet
        guild_id : int
            The ID of the guild the snippet belongs to

        Returns
        -------
        Snippet
            The created snippet
        """
        # Use connect_or_create pattern instead of ensure_guild_exists
        return await self.create(
            data={
                "snippet_name": snippet_name,
                "snippet_content": snippet_content,
                "snippet_created_at": snippet_created_at,
                "snippet_user_id": snippet_user_id,
                "guild": self.connect_or_create_relation("guild_id", guild_id),
                "uses": 0,
                "locked": False,
            },
            include={"guild": True},
        )

    async def get_snippet_by_id(self, snippet_id: int, include_guild: bool = False) -> Snippet | None:
        """Get a snippet by its ID.

        Parameters
        ----------
        snippet_id : int
            The ID of the snippet to get
        include_guild : bool
            Whether to include the guild relation

        Returns
        -------
        Snippet | None
            The snippet if found, None otherwise
        """
        include = {"guild": True} if include_guild else None
        return await self.find_unique(where={"snippet_id": snippet_id}, include=include)

    async def delete_snippet_by_id(self, snippet_id: int) -> Snippet | None:
        """Delete a snippet by its ID.

        Parameters
        ----------
        snippet_id : int
            The ID of the snippet to delete

        Returns
        -------
        Snippet | None
            The deleted snippet if found, None otherwise
        """
        return await self.delete(where={"snippet_id": snippet_id})

    async def create_snippet_alias(
        self,
        snippet_name: str,
        snippet_alias: str,
        snippet_created_at: datetime.datetime,
        snippet_user_id: int,
        guild_id: int,
    ) -> Snippet:
        """Create a new snippet alias.

        Parameters
        ----------
        snippet_name : str
            The name of the snippet this is an alias for.
        snippet_alias : str
            The alias name.
        snippet_created_at : datetime.datetime
            The creation time of the alias.
        snippet_user_id : int
            The ID of the user creating the alias.
        guild_id : int
            The ID of the guild the alias belongs to.

        Returns
        -------
        Snippet
            The created snippet alias record.
        """
        # Use connect_or_create pattern for guild relation
        return await self.create(
            data={
                "snippet_name": snippet_name,
                "alias": snippet_alias,  # Assuming 'alias' is the correct field name
                "snippet_created_at": snippet_created_at,
                "snippet_user_id": snippet_user_id,
                "guild": self.connect_or_create_relation("guild_id", guild_id),
                "uses": 0,  # Set default values
                "locked": False,
            },
            include={"guild": True},
        )

    async def get_all_aliases(self, snippet_name: str, guild_id: int) -> list[Snippet]:
        """Get all aliases for a snippet name within a guild.

        Parameters
        ----------
        snippet_name : str
            The name of the snippet to find aliases for.
        guild_id : int
            The ID of the guild to search within.

        Returns
        -------
        list[Snippet]
            A list of Snippet objects representing the aliases.
        """
        return await self.find_many(
            where={"alias": {"equals": snippet_name, "mode": "insensitive"}, "guild_id": guild_id},
        )

    async def update_snippet_by_id(self, snippet_id: int, snippet_content: str) -> Snippet | None:
        """Update a snippet's content.

        Parameters
        ----------
        snippet_id : int
            The ID of the snippet to update
        snippet_content : str
            The new content for the snippet

        Returns
        -------
        Snippet | None
            The updated snippet if found, None otherwise
        """
        return await self.update(
            where={"snippet_id": snippet_id},
            data={"snippet_content": snippet_content},
        )

    async def increment_snippet_uses(self, snippet_id: int) -> Snippet | None:
        """Increment the use counter for a snippet.

        This method uses a transaction to ensure atomicity.

        Parameters
        ----------
        snippet_id : int
            The ID of the snippet to increment

        Returns
        -------
        Snippet | None
            The updated snippet if found, None otherwise
        """

        async def increment_tx():
            snippet = await self.find_unique(where={"snippet_id": snippet_id})
            if snippet is None:
                return None

            # Safely get the current uses value
            snippet_uses = self.safe_get_attr(snippet, "uses", 0)

            return await self.update(
                where={"snippet_id": snippet_id},
                data={"uses": snippet_uses + 1},
            )

        return await self.execute_transaction(increment_tx)

    async def lock_snippet_by_id(self, snippet_id: int) -> Snippet | None:
        """Lock a snippet.

        Parameters
        ----------
        snippet_id : int
            The ID of the snippet to lock

        Returns
        -------
        Snippet | None
            The updated snippet if found, None otherwise
        """
        return await self.update(
            where={"snippet_id": snippet_id},
            data={"locked": True},
        )

    async def unlock_snippet_by_id(self, snippet_id: int) -> Snippet | None:
        """Unlock a snippet.

        Parameters
        ----------
        snippet_id : int
            The ID of the snippet to unlock

        Returns
        -------
        Snippet | None
            The updated snippet if found, None otherwise
        """
        return await self.update(
            where={"snippet_id": snippet_id},
            data={"locked": False},
        )

    async def toggle_snippet_lock_by_id(self, snippet_id: int) -> Snippet | None:
        """Toggle a snippet's lock state.

        This method uses a transaction to ensure atomicity.

        Parameters
        ----------
        snippet_id : int
            The ID of the snippet to toggle

        Returns
        -------
        Snippet | None
            The updated snippet if found, None otherwise
        """

        async def toggle_lock_tx():
            snippet = await self.find_unique(where={"snippet_id": snippet_id})
            if snippet is None:
                return None

            # Safely get the current locked state
            is_locked = self.safe_get_attr(snippet, "locked", False)

            return await self.update(
                where={"snippet_id": snippet_id},
                data={"locked": not is_locked},
            )

        return await self.execute_transaction(toggle_lock_tx)

    async def count_snippets_by_guild_id(self, guild_id: int) -> int:
        """Count the number of snippets in a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to count snippets for

        Returns
        -------
        int
            The number of snippets in the guild
        """
        return await self.count(where={"guild_id": guild_id})

    async def bulk_delete_snippets_by_guild_id(self, guild_id: int) -> int:
        """Delete all snippets for a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to delete snippets for

        Returns
        -------
        int
            The number of snippets deleted
        """
        return await self.delete_many(where={"guild_id": guild_id})
