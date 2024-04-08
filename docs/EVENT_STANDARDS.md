# Event Listeners

Event listeners are a crucial part of creating dynamic and responsive cogs for the Discord bot. They enable cogs to react automatically to various events within the Discord ecosystem, such as messages being sent, edited, deleted, or users joining/leaving a server.

## Implementing Event Listeners

- To implement an event listener within a cog, use the `@commands.Cog.listener()` decorator above an asynchronous method.
- The method name typically reflects the event it handles (e.g., `on_message_delete` for handling message deletions).
- Each event listener method should accept `self` and the event-specific parameters (e.g., `message: discord.Message` for `on_message_delete`).

### Example:
```python
class MyCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        # Your code here to handle the event
```

## Best Practices

- **Logging**: Use `logger` to log events handled by your listeners for easier debugging and monitoring.
- **Check conditions**: Before executing your logic, check relevant conditions. For example, ignore bot messages to prevent unnecessary processing.
- **Use Embeds for Rich Responses**: If your listener responds in a channel, consider using embeds to make your messages more informative and visually appealing.
- **Permissions and Error Handling**: Ensure your bot has the required permissions for any actions it tries to undertake in response to the event and gracefully handle any exceptions that may occur to prevent the bot from crashing.

### Handling Permissions Example:
```python
@commands.Cog.listener()
async def on_member_join(self, member: discord.Member) -> None:
    try:
        # Attempt to assign a role or send a welcome message
    except discord.Forbidden:
        logger.error(f"Missing permissions to act on member join in {member.guild.name}.")
```

## Example Use Cases

### Monitoring Ghost Pings:
Listen for deleted messages containing pings and notify the channel, providing visibility into ghost pinging activities.

### Welcoming Members:
Automatically assign roles or send a welcome message when new members join the server, enhancing the onboarding experience.

### Custom Role Management:
Dynamically manage roles based on server events, such as creating unique roles for the Nth user to join or modifying roles based on member activities.

By implementing event listeners within your cogs, you contribute to creating an engaging, interactive, and well-moderated Discord community. Always consider the user experience and server performance when designing your listeners, and adhere to Discord's guidelines and rate limits.