import hashlib
import io
from base64 import b64encode
from typing import Any, cast

import cairosvg  # type: ignore
import discord
import httpx
from discord import app_commands
from discord.ext import commands

from tux.utils.embeds import EmbedCreator

client = httpx.AsyncClient()

COLOR_FORMATS = {"HEX": "hex", "RGB": "rgb", "HSL": "hsl", "CMYK": "cmyk"}


class Tools(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.encodings = {
            "base64": self.encode_base64,
            "md5": self.encode_md5,
            "sha256": self.encode_sha256,
            "sha512": self.encode_sha512,
        }

    def encode_base64(self, input_string: str):
        return b64encode(input_string.encode()).decode()

    def encode_md5(self, input_string: str):
        return hashlib.md5(input_string.encode()).hexdigest()

    def encode_sha256(self, input_string: str):
        return hashlib.sha256(input_string.encode()).hexdigest()

    def encode_sha512(self, input_string: str):
        return hashlib.sha512(input_string.encode()).hexdigest()

    group = app_commands.Group(name="tools", description="Various tool commands.")

    @group.command(name="colors", description="Converts a color to different formats.")
    @app_commands.describe(color_format="Original color format to convert from")
    @app_commands.choices(
        color_format=[
            app_commands.Choice[str](name=color_format, value=value)
            for color_format, value in COLOR_FORMATS.items()
        ]
    )
    async def colors(
        self,
        interaction: discord.Interaction,
        color_format: discord.app_commands.Choice[str],
        color: str,
    ) -> None:
        if color_format.value == "HEX" and color.startswith("#"):
            color = color[1:]

        api = f"https://www.thecolorapi.com/id?format=json&{color_format.value}={color}"

        data: Any = await self.make_request(api)
        content: bytes = await self.get_svg_content(data["image"]["named"])
        png_bio: io.BytesIO = self.convert_svg_to_png(content)

        embed = self.construct_embed(interaction, data)
        await self.send_message(interaction, embed, png_bio)

    async def make_request(self, api: str) -> Any:
        return (await client.get(api)).json()

    async def get_svg_content(self, svg_url: str) -> bytes:
        return (await client.get(svg_url)).content

    def convert_svg_to_png(self, content: bytes) -> io.BytesIO:
        # Attempt conversion from SVG to PNG
        png_content = cairosvg.svg2png(bytestring=content, dpi=96, scale=1, unsafe=False)  # type: ignore

        # Ensure the output is bytes; use cast to reassure type checkers
        png_content = cast(bytes | None, png_content)
        if png_content is None:
            msg = "Failed to convert SVG to PNG"
            raise ValueError(msg)

        # Create BytesIO stream from the PNG content bytes
        png_bio = io.BytesIO(png_content)
        png_bio.seek(0)
        return png_bio

    def construct_embed(self, interaction: discord.Interaction, data: Any) -> discord.Embed:
        embed = EmbedCreator.create_info_embed(
            title="Color Converter",
            description="Here is your color converted!",
            interaction=interaction,
        )

        for color_format, value in COLOR_FORMATS.items():
            embed.add_field(name=color_format, value=data[value]["value"])
        embed.add_field(name="HSV", value=data["hsv"]["value"])
        embed.add_field(name="XYZ", value=data["XYZ"]["value"])

        embed.set_thumbnail(url="attachment://color.png")

        return embed

    async def send_message(
        self, interaction: discord.Interaction, embed: discord.Embed, png_bio: io.BytesIO
    ) -> None:
        await interaction.response.send_message(
            embed=embed, file=discord.File(png_bio, "color.png")
        )

    @app_commands.command(name="encode", description="Encodes a string to a specified format.")
    @app_commands.describe(encoding="The encoding format to use", string="The string to encode")
    @app_commands.choices(
        encoding=[
            app_commands.Choice[str](name="base64", value="base64"),
            app_commands.Choice[str](name="md5", value="md5"),
            app_commands.Choice[str](name="sha256", value="sha256"),
            app_commands.Choice[str](name="sha512", value="sha512"),
        ]
    )
    async def encode(
        self,
        interaction: discord.Interaction,
        encoding: app_commands.Choice[str],
        string: str,
    ) -> None:
        title = f"{encoding.name.capitalize()} Encode"
        try:
            encode_func = self.encodings[encoding.value]
            encoded_string = encode_func(string)
            description = f"Encoded: {encoded_string}"
        except KeyError:
            description = "Invalid encoding selected!"

        embed = EmbedCreator.create_info_embed(
            title=title, description=description, interaction=interaction
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Tools(bot))
