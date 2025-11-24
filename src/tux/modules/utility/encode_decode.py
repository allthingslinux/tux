"""
Text encoding and decoding utilities.

This module provides commands for encoding and decoding text using various
algorithms including Base16, Base32, Base64, and Base85 with Discord integration.
"""

import base64
import binascii

from discord import AllowedMentions, app_commands
from discord.ext import commands
from loguru import logger

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.shared.functions import generate_usage


def wrap_strings(wrapper: str, contents: list[str]) -> list[str]:
    """Wrap each string in the list with the specified wrapper string.

    Parameters
    ----------
    wrapper : str
        The string to wrap around each content item.
    contents : list[str]
        List of strings to wrap.

    Returns
    -------
    list[str]
        List of wrapped strings.
    """
    return [f"{wrapper}{content}{wrapper}" for content in contents]


allowed_mentions: AllowedMentions = AllowedMentions(
    everyone=False,
    users=False,
    roles=False,
)

SUPPORTED_FORMATS = [
    app_commands.Choice(name="base16", value="base16"),
    app_commands.Choice(name="base32", value="base32"),
    app_commands.Choice(name="base64", value="base64"),
    app_commands.Choice(name="base85", value="base85"),
]
SUPPORTED_FORMATS_MESSAGE = [
    "base16",
    "base32",
    "base64",
    "base85",
]


class EncodeDecode(BaseCog):
    """Discord cog for text encoding and decoding operations."""

    def __init__(self, bot: Tux) -> None:
        """
        Initialize the EncodeDecode cog.

        Parameters
        ----------
        bot : Tux
            The bot instance.
        """
        self.bot = bot
        self.encode.usage = generate_usage(self.encode)
        self.decode.usage = generate_usage(self.decode)

    async def send_message(self, ctx: commands.Context[Tux], data: str):
        """Reply to the context with the encoded or decoded data.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        data : str
            The data to send.
        """
        if len(data) > 2000:
            logger.debug(
                f"Encode/decode output too long ({len(data)} chars) for {ctx.author.id}",
            )
            await ctx.reply(
                content="The string ended up being too long. Please use this [site](https://www.base64encode.org/) instead.",
                allowed_mentions=allowed_mentions,
                ephemeral=True,
            )
            return

        await ctx.reply(
            content=data,
            allowed_mentions=allowed_mentions,
            ephemeral=True,
            suppress_embeds=True,
        )

    @commands.hybrid_command(
        name="encode",
        aliases=["ec"],
        description="Encode a message",
    )
    @app_commands.describe(encoding="Which format to use")
    @app_commands.describe(text="Text to encode")
    @app_commands.choices(encoding=SUPPORTED_FORMATS)
    async def encode(
        self,
        ctx: commands.Context[Tux],
        encoding: str,
        *,
        text: str,
    ) -> None:
        """
        Encode text in a coding system.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        encoding: str
            The encoding method (can be base16, base32, base64, or base85).
        text : str
            The text you want to encode.
        """
        encoding = encoding.lower()
        btext = text.encode(encoding="utf-8")

        logger.debug(
            f"Encoding request: {encoding} from {ctx.author.name} ({ctx.author.id}), text length: {len(text)}",
        )

        try:
            if encoding == "base16":
                data = base64.b16encode(btext)
            elif encoding == "base32":
                data = base64.b32encode(btext)
            elif encoding == "base64":
                data = base64.b64encode(btext)
            elif encoding == "base85":
                data = base64.b85encode(btext)
            else:
                logger.warning(
                    f"Invalid encoding '{encoding}' requested by {ctx.author.id}",
                )
                await ctx.reply(
                    content=f"Invalid encoding {', '.join(wrap_strings('`', SUPPORTED_FORMATS_MESSAGE))} are supported.",
                    allowed_mentions=allowed_mentions,
                    ephemeral=True,
                )
                return

            logger.debug(f"Encoding successful: {encoding}, output length: {len(data)}")
            await self.send_message(ctx, data.decode(encoding="utf-8"))
        except Exception as e:
            logger.error(f"Encoding error ({encoding}): {type(e).__name__}: {e}")
            await ctx.reply(
                content=f"Unknown exception: {type(e)}: {e}",
                allowed_mentions=allowed_mentions,
                ephemeral=True,
            )

    @commands.hybrid_command(
        name="decode",
        aliases=["dc"],
        description="Decode a message",
    )
    @app_commands.describe(encoding="Which format to use")
    @app_commands.describe(text="Text to decode")
    @app_commands.choices(encoding=SUPPORTED_FORMATS)
    async def decode(
        self,
        ctx: commands.Context[Tux],
        encoding: str,
        *,
        text: str,
    ) -> None:
        """
        Decode text in a coding system.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        encoding : str
            The encoding method (can be base16, base32, base64, or base85).
        text : str
            The text you want to decode.
        """
        encoding = encoding.lower()
        btext = text.encode(encoding="utf-8")

        logger.debug(
            f"Decoding request: {encoding} from {ctx.author.name} ({ctx.author.id}), text length: {len(text)}",
        )

        try:
            if encoding == "base16":
                data = base64.b16decode(btext)
            elif encoding == "base32":
                data = base64.b32decode(btext)
            elif encoding == "base64":
                data = base64.b64decode(btext)
            elif encoding == "base85":
                data = base64.b85decode(btext)
            else:
                logger.warning(
                    f"Invalid decoding format '{encoding}' requested by {ctx.author.id}",
                )
                await ctx.reply(
                    content=f"Invalid encoding {', '.join(wrap_strings('`', SUPPORTED_FORMATS_MESSAGE))} are supported.",
                    allowed_mentions=allowed_mentions,
                    ephemeral=True,
                )
                return

            logger.debug(f"Decoding successful: {encoding}, output length: {len(data)}")
            await self.send_message(ctx, data.decode(encoding="utf-8"))
        except binascii.Error as e:
            logger.warning(f"Decoding error for {encoding} from {ctx.author.id}: {e}")
            await ctx.reply(
                content=f"Decoding error: {e}",
                ephemeral=True,
            )
            return
        except UnicodeDecodeError as e:
            logger.warning(
                f"Invalid UTF-8 output after {encoding} decode from {ctx.author.id}: {e}",
            )
            await ctx.reply(
                content="The message was decoded, but the output is not valid UTF-8.",
                allowed_mentions=allowed_mentions,
                ephemeral=True,
            )
        except Exception as e:
            logger.error(
                f"Unexpected decoding error ({encoding}): {type(e).__name__}: {e}",
            )
            await ctx.reply(
                content=f"Unknown exception: {type(e)}: {e}",
                allowed_mentions=allowed_mentions,
                ephemeral=True,
            )


async def setup(bot: Tux) -> None:
    """Set up the EncodeDecode cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(EncodeDecode(bot))
