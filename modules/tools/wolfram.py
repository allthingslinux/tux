import asyncio
import io
from urllib.parse import quote_plus

import aiohttp
import discord
from bot import Tux
from discord import app_commands
from discord.ext import commands
from loguru import logger
from PIL import Image
from ui.embeds import EmbedCreator
from utils.config import CONFIG


class Wolfram(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot

        # Verify AppID configuration; unload cog if missing
        if not CONFIG.WOLFRAM_APP_ID:
            logger.warning("Wolfram Alpha API ID is not set. Some Science/Math commands will not work.")
            # Store the task reference
            self._unload_task = asyncio.create_task(self._unload_self())
        else:
            logger.info("Wolfram Alpha API ID is set, Science/Math commands that depend on it will work.")

    async def _unload_self(self):
        """Unload this cog if configuration is missing."""
        try:
            await self.bot.unload_extension("tux.cogs.tools.wolfram")
            logger.info("Wolfram cog has been unloaded due to missing configuration")
        except Exception as e:
            logger.error(f"Failed to unload Wolfram cog: {e}")

    @commands.hybrid_command(name="wolfram", description="Query Wolfram|Alpha Simple API and return an image result.")
    @app_commands.describe(
        query="The input query for Wolfram|Alpha, e.g. 'integrate x^2' or 'What is the capital of France?'",
    )
    async def wolfram(self, ctx: commands.Context[Tux], *, query: str) -> None:
        """
        Send a query to Wolfram|Alpha Simple API and return the visual result.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            Invocation context for the command.
        query : str
            Input string for the Wolfram|Alpha query, e.g. 'integrate x^2'.
        """

        await ctx.defer()

        # Build the Simple API endpoint URL with URL-encoded query
        encoded = quote_plus(query)
        url = f"https://api.wolframalpha.com/v1/simple?appid={CONFIG.WOLFRAM_APP_ID}&i={encoded}"

        try:
            # Perform async HTTP GET with a 10-second timeout
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession() as session, session.get(url, timeout=timeout) as resp:
                resp.raise_for_status()
                img_data = await resp.read()
        except Exception:
            # On error, notify user via an error embed
            embed = EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedCreator.ERROR,
                user_name=ctx.author.name,
                user_display_avatar=ctx.author.display_avatar.url,
                description="Failed to retrieve image from Wolfram|Alpha Simple API.",
            )
            await ctx.send(embed=embed)
            return

        # Crop the top 80 pixels from the fetched image
        image = Image.open(io.BytesIO(img_data))
        width, height = image.size
        cropped = image.crop((0, 80, width, height))
        buffer = io.BytesIO()
        cropped.save(buffer, format=image.format or "PNG")
        buffer.seek(0)
        image_file = discord.File(buffer, filename="wolfram.png")

        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.INFO,
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
            title=f"Wolfram|Alpha: {query}",
        )
        # Display the image via embed attachment URL
        embed.set_image(url="attachment://wolfram.png")
        await ctx.send(embed=embed, file=image_file)


async def setup(bot: Tux) -> None:
    await bot.add_cog(Wolfram(bot))
