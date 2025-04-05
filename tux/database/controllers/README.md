# Database Controllers

This directory contains the database controllers for the Tux application. Each controller provides a standardized interface for interacting with a specific database model.

## Core Design Patterns

### BaseController Architecture

All controllers extend the `BaseController` class, which provides:

- Common CRUD operations (create, read, update, delete)
- Standardized error handling
- Type safety through generics
- Transaction support
- Utility methods for common patterns

```python
class MyController(BaseController[MyModel]):
    def __init__(self):
        super().__init__("my_model_table_name")
```

### Relations Management

For creating or connecting to related entities, always use the `connect_or_create_relation` utility method:

```python
# Instead of manually creating the relation
"guild": {
    "connect_or_create": {
        "where": {"guild_id": guild_id},
        "create": {"guild_id": guild_id},
    },
}

# Use the utility method
"guild": self.connect_or_create_relation("guild_id", guild_id)
```

### Transaction Support

For operations that require atomicity (lookup + update), use transactions:

```python
async def update_entity(self, entity_id: int, data: dict[str, Any]) -> Entity | None:
    async def update_tx():
        entity = await self.find_unique(where={"id": entity_id})
        if entity is None:
            return None
        
        return await self.update(where={"id": entity_id}, data=data)
        
    return await self.execute_transaction(update_tx)
```

### Safe Attribute Access

Always use `safe_get_attr` to access model attributes, to handle missing values gracefully:

```python
# Instead of directly accessing attributes
count = entity.count + 1

# Use safe_get_attr
count = self.safe_get_attr(entity, "count", 0) + 1
```

## Best Practices

1. **Unique Identifiers**: Use `find_unique` for primary key lookups
2. **Relation Handling**: Always use `connect_or_create_relation` to prevent race conditions
3. **Batch Operations**: Use `update_many` and `delete_many` for bulk operations
4. **Transactions**: Wrap operations that include lookup + modification in transactions
5. **Error Handling**: Let the base controller handle errors, but add context where needed
6. **Documentation**: Document all public methods with NumPy-style docstrings
7. **Type Safety**: Use proper typing for parameters and return values

## Common Controller Methods

All controllers should implement these methods if they apply:

1. CRUD Operations:
   - `get_<entity>_by_id` - Get by primary key
   - `get_all_<entities>` - Get all entities
   - `get_<entity>_by_<field>` - Get by specific field
   - `create_<entity>` - Create new entity
   - `update_<entity>` - Update existing entity
   - `delete_<entity>` - Delete entity

2. Relation Operations:
   - Methods that create or update entities with relations
   - Methods that query based on related entities

3. Bulk Operations:
   - `bulk_delete_<entities>_by_<field>` - Bulk delete
   - `count_<entities>_by_<field>` - Count entities

## Usage Examples

### Creating an Entity with Relations

```python
async def create_case(self, guild_id: int, user_id: int) -> Case:
    return await self.create(
        data={
            "case_number": 1,
            "user_id": user_id,
            "guild": self.connect_or_create_relation("guild_id", guild_id),
        },
        include={"guild": True},
    )
```

### Finding an Entity with Pagination

```python
async def get_recent_cases(self, guild_id: int, limit: int = 10) -> list[Case]:
    return await self.find_many(
        where={"guild_id": guild_id},
        order={"created_at": "desc"},
        take=limit,
    )
```

### Using Transactions

```python
async def update_score(self, user_id: int, points: int) -> User | None:
    async def update_tx():
        user = await self.find_unique(where={"id": user_id})
        if user is None:
            return None
        
        current_score = self.safe_get_attr(user, "score", 0)
        return await self.update(
            where={"id": user_id},
            data={"score": current_score + points},
        )
        
    return await self.execute_transaction(update_tx)
```
