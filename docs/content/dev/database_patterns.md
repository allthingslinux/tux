# Database Controller Patterns

This document outlines the core design patterns, best practices, and common methods used within the database controllers located in `tux/database/controllers/`. These controllers provide a standardized interface for interacting with specific database models.

## Core Design Patterns

### BaseController Architecture

All controllers extend the `BaseController` class ([`tux/database/controllers/base.py`](https://github.com/allthingslinux/tux/blob/main/tux/database/controllers/base.py)), which provides:

- Common CRUD operations (create, read, update, delete)
- Standardized error handling
- Type safety through generics
- Transaction support
- Utility methods for common patterns

```python
# Example Structure
from tux.database.controllers.base import BaseController
from prisma.models import YourModel

class YourController(BaseController[YourModel]):
    def __init__(self):
        # Initialize with the Prisma model name (lowercase table name)
        super().__init__("yourModel") # Corresponds to YourModel in Prisma schema
```

### Relations Management

For creating or connecting to related entities (handling foreign keys), always use the `connect_or_create_relation` utility method provided by the `BaseController`. This helps prevent race conditions and ensures consistency.

```python
# Example: Creating a Case linked to a Guild

# Instead of manually crafting the nested write:
# "guild": {
#     "connect_or_create": {
#         "where": {"guild_id": guild_id},
#         "create": {"guild_id": guild_id},
#     },
# }

# Use the utility method:
await self.create(
    data={
        "case_number": 1,
        "user_id": user_id,
        "guild": self.connect_or_create_relation("guild_id", guild_id),
    },
    include={"guild": True}, # Optionally include the related model in the result
)
```

### Transaction Support

For operations that require atomicity (e.g., reading a value then updating it based on the read value), use transactions via the `execute_transaction` method. Pass an async function containing the transactional logic.

```python
async def update_score(self, user_id: int, points_to_add: int) -> User | None:
    async def update_tx():
        user = await self.find_unique(where={"id": user_id})
        if user is None:
            return None # Entity not found

        # Use safe_get_attr for potentially missing attributes
        current_score = self.safe_get_attr(user, "score", 0)

        # Perform the update within the transaction
        return await self.update(
            where={"id": user_id},
            data={"score": current_score + points_to_add},
        )

    # Execute the transaction
    return await self.execute_transaction(update_tx)
```

### Safe Attribute Access

When accessing attributes from a model instance returned by Prisma, especially optional fields or fields within included relations, use `safe_get_attr` to handle `None` values or potentially missing attributes gracefully by providing a default value.

```python
# Instead of risking AttributeError or TypeError:
# count = entity.count + 1

# Use safe_get_attr:
count = self.safe_get_attr(entity, "count", 0) + 1
```

## Best Practices

1. **Unique Identifiers**: Use `find_unique` for lookups based on primary keys or `@unique` fields defined in your Prisma schema.
2. **Relation Handling**: Always use `connect_or_create_relation` when creating/updating entities with foreign key relationships.
3. **Batch Operations**: Utilize `update_many` and `delete_many` for bulk operations where applicable to improve performance.
4. **Transactions**: Wrap sequences of operations that must succeed or fail together (especially read-modify-write patterns) in `execute_transaction`.
5. **Error Handling**: Leverage the `BaseController`'s error handling. Add specific `try...except` blocks within controller methods only if custom error logging or handling is needed beyond the base implementation.
6. **Documentation**: Document all public controller methods using NumPy-style docstrings, explaining parameters, return values, and potential exceptions.
7. **Type Safety**: Use specific Prisma model types (e.g., `prisma.models.User`) and type hints for parameters and return values.

## Common Controller Methods

While the `BaseController` provides generic `create`, `find_unique`, `find_many`, `update`, `delete`, etc., individual controllers should implement more specific, intention-revealing methods where appropriate. Examples:

1. **Specific Getters:**
    - `get_user_by_discord_id(discord_id: int) -> User | None:` (Uses `find_unique` internally)
    - `get_active_cases_for_user(user_id: int, guild_id: int) -> list[Case]:` (Uses `find_many` with specific `where` clauses)
    - `get_all_settings() -> list[Setting]:`

2. **Specific Creators/Updaters:**
    - `create_user_profile(discord_id: int, display_name: str) -> User:`
    - `increment_user_xp(user_id: int, amount: int) -> User | None:` (Likely uses a transaction)
    - `update_setting(key: str, value: str) -> Setting | None:`

3. **Specific Deletions:**
    - `delete_case_by_id(case_id: int) -> Case | None:`
    - `bulk_delete_user_data(user_id: int) -> None:` (May involve multiple `delete_many` calls)

4. **Counting Methods:**
    - `count_warnings_for_user(user_id: int, guild_id: int) -> int:`

## Usage Examples

### Creating an Entity with Relations

```python
# From CaseController
async def create_new_case(self, guild_id: int, user_id: int, moderator_id: int, reason: str) -> Case:
    # Determine the next case number (might involve a lookup or transaction)
    next_case_num = await self.get_next_case_number(guild_id) 

    return await self.create(
        data={
            "case_number": next_case_num,
            "reason": reason,
            "user": self.connect_or_create_relation("user_id", user_id), # Connect user
            "moderator": self.connect_or_create_relation("moderator_id", moderator_id), # Connect moderator
            "guild": self.connect_or_create_relation("guild_id", guild_id), # Connect guild
        },
        include={"guild": True, "user": True, "moderator": True}, # Include relations in result
    )
```

### Finding Entities with Pagination/Ordering

```python
# From CaseController
async def get_recent_cases(self, guild_id: int, limit: int = 10) -> list[Case]:
    return await self.find_many(
        where={"guild_id": guild_id},
        order={"created_at": "desc"}, # Order by creation date, newest first
        take=limit, # Limit the number of results
    )
```

### Using Transactions for Atomic Updates

```python
# From UserController
async def increment_xp(self, user_id: int, xp_to_add: int) -> User | None:
    async def update_tx():
        user = await self.find_unique(where={"id": user_id})
        if user is None:
            # Optionally create the user here if they don't exist, or return None
            return None

        current_xp = self.safe_get_attr(user, "xp", 0)
        return await self.update(
            where={"id": user_id},
            data={"xp": current_xp + xp_to_add},
        )

    return await self.execute_transaction(update_tx)
```
