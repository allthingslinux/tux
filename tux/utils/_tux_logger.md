# TuxLogger Documentation

## Usage Instructions

Hey contributor, Ty here! To use the logger in your cog files, please follow these steps:

1. Import the logger by adding the following line at the top of your main bot file:

    ```python
    from your_module_name import logger
    ```

2. Once imported, you can use the logger to log messages in your code. For example:

    ```python
    logger.info("This is an information message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.debug("This is a debug message.")
    ```

### Logger setup

```python
    async def setup(bot,
        project_logging_level=logging.DEBUG,
        discord_logging_level=logging.WARNING):
```

1. bot: The Discord bot instance.
1. project_logging_level: The logging level for the project (default is DEBUG).
1. discord_logging_level: The logging level for the Discord library (default is WARNING).

I love you all and thank you for contributing <3
