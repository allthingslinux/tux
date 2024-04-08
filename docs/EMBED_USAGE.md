# EMBED_USAGE.md

Welcome to the usage guidelines of our `EmbedCreator` utility for the Discord bot project. This document is designed to help you understand how to use the `EmbedCreator` class effectively to generate and customize embeds within your commands and interactions. We will use the `Poll` cog as an example to illustrate these concepts.

## EmbedCreator Basic Usage

The `EmbedCreator` class in our project simplifies the process of creating embeds for different purposes, such as informational messages, errors, warnings, success confirmations, and polls. Here's a step-by-step guide on using it in your commands:

### Step 1: Import EmbedCreator

First, ensure you import the `EmbedCreator` class in your cog or wherever you intend to use it:

```python
from tux.utils.embeds import EmbedCreator
```

### Step 2: Create an Embed

Decide on the type of embed you want to create based on the context. For instance, if you're creating a poll, you'd use `create_poll_embed` method. Here's how you can create a basic poll embed:

```python
embed = EmbedCreator.create_poll_embed(
    title="Your Poll Title",
    description="Your Poll Description",
    interaction=interaction,
)
```

Replace `"Your Poll Title"` and `"Your Poll Description"` with your poll's title and options respectively. The `interaction` parameter is the Discord interaction object received in your command function.

### Step 3: Sending the Embed

Once the embed is created, you can send it as part of the interaction response:

```python
await interaction.response.send_message(embed=embed)
```

For asynchronous commands or events, remember to `await` the sending operation.

### Step 4: Adding Reactions for Polls

If your embed is a poll, you’ll likely want to add reactions that users can click on to vote. Here's an example code snippet to add reactions for option numbers:

```python
message = await interaction.original_response()
options_list = ["Option 1", "Option 2", "Option 3"]  # Your poll options list
for num in range(len(options_list)):
    await message.add_reaction(f"{num + 1}\u20e3")
```

This block of code fetches the message associated with the original response and loops through the options, adding a corresponding numeric reaction for each.

### Error Handling Example

Here's an example of using `EmbedCreator` to handle an error case where the user provides an invalid number of options for the poll:

```python
if len(options_list) < 2 or len(options_list) > 9:
    embed = EmbedCreator.create_error_embed(
        title="Invalid options count",
        description=f"Poll options count needs to be between 2-9, you provided {len(options_list)} options.",
        interaction=interaction,
    )

    await interaction.response.send_message(embed=embed)
    return
```

This checks if the number of options is outside the allowable range, and if so, sends an error message.

## Best Practices

- **Appropriate Use of Embed Types**: Choose the embed type that best suits the context of your message (e.g., use error embeds for errors, info embeds for informational messages).
- **Performance Considerations**: While adding reactions or performing other operations, be mindful of rate limits and performance implications.
- **User Experience**: Ensure that your embeds and responses are user-friendly, providing clear and concise information that enhances the interaction flow.

## Conclusion

The `EmbedCreator` utility aims to standardize and simplify the process of creating embeds across our Discord bot project. By following these guidelines and best practices, you can ensure consistent, efficient, and effective use of embeds to enhance user interactions and functionality. Remember to review your code for adherence to these guidelines and adapt them as necessary to fit your specific use cases.