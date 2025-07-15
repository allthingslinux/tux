import base64
import binascii

from discord import AllowedMentions
from discord.ext import commands

from tux.bot import Tux
from tux.utils.functions import generate_usage


def wrap_strings(wrapper: str, contents: list[str]) -> list[str]:
    return [f"{wrapper}{content}{wrapper}" for content in contents]


allowed_mentions: AllowedMentions = AllowedMentions(
    everyone=False,
    users=False,
    roles=False,
)

CODING_SYSTEMS = [
    "base16",
    "base32",
    "base64",
    "base85",
]


class EncodeDecode(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.encode.usage = generate_usage(self.encode)
        self.decode.usage = generate_usage(self.decode)

    async def send_message(self, ctx: commands.Context[Tux], data: str):
        if len(data) > 2000:
            await ctx.reply(
                content="The string ended up being too long. Please use this [site](https://www.base64encode.org/) instead.",
                allowed_mentions=allowed_mentions,
                ephemeral=True,
            )
            return

        await ctx.reply(
            content=data,
            allowed_mentions=allowed_mentions,
            ephemeral=False,
        )

    @commands.hybrid_command(
        name="encode",
    )
    async def encode(
        self,
        ctx: commands.Context[Tux],
        cs: str,
        *,
        text: str,
    ) -> None:
        """
        Encode text in a coding system.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        cs : str
            The coding system.
        text : str
            The text you want to encode.
        """

        cs = cs.lower()
        btext = text.encode(encoding="utf-8")

        try:
            if cs == "base16":
                data = base64.b16encode(btext)
            elif cs == "base32":
                data = base64.b32encode(btext)
            elif cs == "base64":
                data = base64.b64encode(btext)
            elif cs == "base85":
                data = base64.b85encode(btext)
            else:
                await ctx.reply(
                    content=f"Invalid coding system. Please use: {', '.join(wrap_strings('`', CODING_SYSTEMS))}",
                    allowed_mentions=allowed_mentions,
                    ephemeral=True,
                )
                return

            await self.send_message(ctx, data.decode(encoding="utf-8"))
        except Exception as e:
            await ctx.reply(
                content=f"Unknown excpetion: {type(e)}: {e}",
                allowed_mentions=allowed_mentions,
                ephemeral=True,
            )

    @commands.hybrid_command(
        name="decode",
    )
    async def decode(
        self,
        ctx: commands.Context[Tux],
        cs: str,
        *,
        text: str,
    ) -> None:
        """
        Decode text in a coding system.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        cs : str
            The coding system.
        text : str
            The text you want to decode.
        """

        cs = cs.lower()
        btext = text.encode(encoding="utf-8")

        try:
            if cs == "base16":
                data = base64.b16decode(btext)
            elif cs == "base32":
                data = base64.b32decode(btext)
            elif cs == "base64":
                data = base64.b64decode(btext)
            elif cs == "base85":
                data = base64.b85decode(btext)
            else:
                await ctx.reply(
                    content=f"Invalid coding system. Please use: {', '.join(wrap_strings('`', CODING_SYSTEMS))}",
                    allowed_mentions=allowed_mentions,
                    ephemeral=True,
                )
                return

            await self.send_message(ctx, data.decode(encoding="utf-8"))
        except binascii.Error as e:
            await ctx.reply(
                content=f"Decoding error: {e}",
            )
            return
        except UnicodeDecodeError:
            await ctx.reply(
                content="The message was decoded, but the output is not valid UTF-8.",
                allowed_mentions=allowed_mentions,
                ephemeral=True,
            )
        except Exception as e:
            await ctx.reply(
                content=f"Unknown excpetion: {type(e)}: {e}",
                allowed_mentions=allowed_mentions,
                ephemeral=True,
            )


async def setup(bot: Tux):
    await bot.add_cog(EncodeDecode(bot))
