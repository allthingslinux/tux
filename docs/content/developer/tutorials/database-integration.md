# Database Integration

Learn how to integrate database functionality into your Tux cogs.

## Prerequisites

Before starting this tutorial, make sure you have:

- Completed the [Creating Your First Cog](creating-first-cog.md) tutorial
- Understanding of SQL basics
- Familiarity with async/await in Python

## Database Setup

### Using Tux's Database Service

Tux provides a built-in database service that handles connections and transactions:

```python
from tux.services.database import DatabaseService
from tux.models.base import BaseModel

class MyCog(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.db = DatabaseService()
```

## Step 1: Creating Models

Define your data models:

```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from tux.models.base import BaseModel

class UserProfile(BaseModel):
    __tablename__ = "user_profiles"
    
    user_id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False)
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
```

## Step 2: Basic Database Operations

### Creating Records

```python
@commands.command(name="register")
async def register_command(self, ctx):
    """Register a user profile."""
    try:
        # Check if user already exists
        existing = await self.db.get(UserProfile, user_id=ctx.author.id)
        if existing:
            await ctx.send("You're already registered!")
            return
        
        # Create new profile
        profile = UserProfile(
            user_id=ctx.author.id,
            username=ctx.author.name,
            level=1,
            experience=0
        )
        
        await self.db.add(profile)
        await ctx.send("Profile created successfully!")
        
    except Exception as e:
        await ctx.send(f"Error creating profile: {e}")
```

### Reading Records

```python
@commands.command(name="profile")
async def profile_command(self, ctx, member: discord.Member = None):
    """View user profile."""
    member = member or ctx.author
    
    try:
        profile = await self.db.get(UserProfile, user_id=member.id)
        if not profile:
            await ctx.send("User not registered!")
            return
        
        embed = TuxEmbed(
            title=f"{member.display_name}'s Profile",
            description=f"Level: {profile.level}\nExperience: {profile.experience}"
        )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"Error fetching profile: {e}")
```

### Updating Records

```python
@commands.command(name="addxp")
async def add_xp_command(self, ctx, amount: int):
    """Add experience points."""
    try:
        profile = await self.db.get(UserProfile, user_id=ctx.author.id)
        if not profile:
            await ctx.send("You need to register first!")
            return
        
        profile.experience += amount
        
        # Check for level up
        new_level = profile.experience // 100 + 1
        if new_level > profile.level:
            profile.level = new_level
            await ctx.send(f"Level up! You're now level {new_level}!")
        else:
            await ctx.send(f"Added {amount} XP!")
        
        await self.db.commit()
        
    except Exception as e:
        await ctx.send(f"Error updating profile: {e}")
```

## Step 3: Advanced Queries

### Complex Queries

```python
@commands.command(name="leaderboard")
async def leaderboard_command(self, ctx):
    """Show top 10 users by level."""
    try:
        # Get top 10 users
        profiles = await self.db.query(
            UserProfile
        ).order_by(
            UserProfile.level.desc(),
            UserProfile.experience.desc()
        ).limit(10).all()
        
        embed = TuxEmbed(title="Leaderboard")
        
        for i, profile in enumerate(profiles, 1):
            user = self.bot.get_user(profile.user_id)
            username = user.display_name if user else "Unknown"
            
            embed.add_field(
                name=f"{i}. {username}",
                value=f"Level {profile.level} ({profile.experience} XP)",
                inline=False
            )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"Error fetching leaderboard: {e}")
```

### Filtered Queries

```python
@commands.command(name="search")
async def search_command(self, ctx, *, query: str):
    """Search for users by username."""
    try:
        profiles = await self.db.query(
            UserProfile
        ).filter(
            UserProfile.username.ilike(f"%{query}%")
        ).limit(5).all()
        
        if not profiles:
            await ctx.send("No users found!")
            return
        
        embed = TuxEmbed(title=f"Search Results for '{query}'")
        
        for profile in profiles:
            user = self.bot.get_user(profile.user_id)
            username = user.display_name if user else profile.username
            
            embed.add_field(
                name=username,
                value=f"Level {profile.level}",
                inline=True
            )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"Error searching: {e}")
```

## Step 4: Transactions

### Using Transactions

```python
@commands.command(name="transfer")
async def transfer_command(self, ctx, recipient: discord.Member, amount: int):
    """Transfer XP to another user."""
    try:
        async with self.db.transaction():
            # Get sender profile
            sender_profile = await self.db.get(UserProfile, user_id=ctx.author.id)
            if not sender_profile or sender_profile.experience < amount:
                await ctx.send("Insufficient XP!")
                return
            
            # Get recipient profile
            recipient_profile = await self.db.get(UserProfile, user_id=recipient.id)
            if not recipient_profile:
                await ctx.send("Recipient not registered!")
                return
            
            # Transfer XP
            sender_profile.experience -= amount
            recipient_profile.experience += amount
            
            await ctx.send(f"Transferred {amount} XP to {recipient.display_name}!")
            
    except Exception as e:
        await ctx.send(f"Transfer failed: {e}")
```

## Step 5: Error Handling

### Database Error Handling

```python
from sqlalchemy.exc import IntegrityError, OperationalError

@commands.command(name="safe-register")
async def safe_register_command(self, ctx):
    """Safely register a user with proper error handling."""
    try:
        profile = UserProfile(
            user_id=ctx.author.id,
            username=ctx.author.name
        )
        
        await self.db.add(profile)
        await ctx.send("Registration successful!")
        
    except IntegrityError:
        await ctx.send("You're already registered!")
    except OperationalError:
        await ctx.send("Database connection error. Please try again later.")
    except Exception as e:
        self.bot.logger.error(f"Unexpected error in register: {e}")
        await ctx.send("An unexpected error occurred.")
```

## Best Practices

### Performance

- Use indexes on frequently queried columns
- Limit query results when possible
- Use transactions for related operations
- Cache frequently accessed data

### Security

- Validate all user input
- Use parameterized queries
- Sanitize data before storage
- Implement proper access controls

### Maintenance

- Use migrations for schema changes
- Backup data regularly
- Monitor database performance
- Log database operations

## Next Steps

After completing this tutorial:

- Learn about [UI Components Walkthrough](ui-components-walkthrough.md)
- Explore [Testing Setup](testing-setup.md)
- Check out the [Database Operations Guide](../guides/database-operations.md) for advanced patterns
- Review [Database Architecture](../concepts/database/index.md) for deeper understanding
