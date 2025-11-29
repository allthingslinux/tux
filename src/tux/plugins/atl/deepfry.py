"""
Deepfry Plugin for Tux Bot.

This plugin provides image deepfrying effects using PIL to apply various
image processing transformations that create a "deepfried" visual effect,
including saturation, contrast, and color adjustments.
"""

import io
from typing import Any

import discord
from discord.ext import commands
from loguru import logger
from PIL import Image, ImageEnhance, ImageOps, ImageSequence

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.services.http_client import http_client
from tux.ui.embeds import EmbedCreator

# JPEG quality (low quality for deepfry aesthetic, but not so low it hurts compression)
JPEG_QUALITY = 1
# AVIF quality (lower = smaller file, range 0-100, 30 is good for deepfry aesthetic)
AVIF_QUALITY = 1


class Deepfry(BaseCog):
    """Image deepfrying effects for Discord."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the Deepfry plugin.

        Parameters
        ----------
        bot : Tux
            The bot instance to initialize the plugin with.
        """
        super().__init__(bot)

    @commands.hybrid_command(
        name="deepfry",
        description="Deepfry an image",
        aliases=["df"],
    )
    async def deepfry(
        self,
        ctx: commands.Context[Any],
        image: discord.Attachment,
    ) -> None:
        """Deepfry an image using various image processing effects."""
        # Extract image URL from the attachment
        image_url = self._extract_image_url(ctx, image)
        pil_image = await self._fetch_image(image_url)

        # Defer for slash commands
        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=True)

        try:
            pil_image.load()
        except Exception as e:
            await self._send_error_embed(
                ctx,
                "Invalid File",
                f"The file is not a valid image. {e}",
            )
            return

        if getattr(pil_image, "is_animated", False):
            try:
                frames: list[Image.Image] = []
                durations: list[int] = []
                for frame in ImageSequence.Iterator(pil_image):
                    processed = self._deepfry_image(frame.convert("RGB"))
                    frames.append(processed)
                    durations.append(frame.info.get("duration", 50))

                if not frames:
                    await self._send_error_embed(
                        ctx,
                        "Invalid GIF",
                        "The animated image has no frames.",
                    )
                    return

                await self._send_animated_result(ctx, frames, durations)
            except Exception as e:
                logger.error(f"Error processing deepfry: {e}")
                await self._send_error_embed(
                    ctx,
                    "Error",
                    "An error occurred while processing the image.",
                )
        else:
            # Process the image
            try:
                deepfried_image = self._deepfry_image(pil_image)
                await self._send_image_result(ctx, deepfried_image)
            except Exception as e:
                logger.error(f"Error processing deepfry: {e}")
                await self._send_error_embed(
                    ctx,
                    "Error",
                    "An error occurred while processing the image.",
                )

    def _extract_image_url(
        self,
        ctx: commands.Context[Any],
        image: discord.Attachment,
    ) -> str:
        """
        Extract image URL from the attachment.

        Returns
        -------
        str
            The URL of the image attachment.
        """
        return image.url

    async def _fetch_image(self, url: str) -> Image.Image:
        """
        Fetch and load an image from URL.

        Returns
        -------
        Image.Image
            The loaded PIL Image object.
        """
        response = await http_client.get(url)
        return Image.open(io.BytesIO(response.content))

    def _deepfry_image(self, image: Image.Image) -> Image.Image:
        """
        Apply deepfry effects to an image.

        Parameters
        ----------
        image : Image.Image
            The image to process.

        Returns
        -------
        Image.Image
            The deepfried image.
        """
        image = image.convert("RGB")
        # Store original size to restore later
        original_size = image.size

        # Downscale for processing (25% of current size)
        image = image.resize(
            (int(image.width * 0.25), int(image.height * 0.25)),
            Image.Resampling.LANCZOS,
        )
        image = ImageEnhance.Sharpness(image).enhance(100.0)

        # Extract red channel and enhance
        r = image.split()[0]
        r = ImageEnhance.Contrast(r).enhance(2.0)
        r = ImageEnhance.Brightness(r).enhance(1.5)

        # Colorize with deepfry colors
        r = ImageOps.colorize(r, "#fe0002", "#ffff0f")  # (254, 0, 2) and (255, 255, 15)
        image = Image.blend(image, r, 0.75)

        # Upscale back to original size
        return image.resize(original_size, Image.Resampling.LANCZOS)

    async def _send_error_embed(
        self,
        ctx: commands.Context[Any],
        title: str,
        description: str,
    ) -> None:
        """Send a standardized error embed."""
        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.ERROR,
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
            title=title,
            description=description,
        )

        if ctx.interaction:
            if not ctx.interaction.response.is_done():
                await ctx.interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await ctx.interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await ctx.send(embed=embed)

    async def _send_image_result(
        self,
        ctx: commands.Context[Any],
        image: Image.Image,
    ) -> None:
        """Send the processed image result."""
        buffer = io.BytesIO()
        image.save(
            buffer,
            format="JPEG",
            quality=JPEG_QUALITY,
            optimize=True,
            progressive=True,
        )
        buffer.seek(0)

        file = discord.File(buffer, filename="deepfried.jpg")

        if ctx.interaction:
            await ctx.interaction.followup.send(file=file, ephemeral=True)
        else:
            await ctx.send(file=file)

    async def _send_animated_result(
        self,
        ctx: commands.Context[Any],
        frames: list[Image.Image],
        durations: list[int],
    ) -> None:
        """Send the processed animated AVIF result."""
        buffer = io.BytesIO()
        frames[0].save(
            buffer,
            format="AVIF",  # SIGNIFICANTLY better compression compared to GIF
            save_all=True,
            append_images=frames[1:],
            loop=0,
            duration=durations,
            disposal=2,
            quality=AVIF_QUALITY,
            speed=6,  # Higher speed = faster encoding, slightly larger files (0-8)
        )
        buffer.seek(0)

        file = discord.File(buffer, filename="deepfried.avif")

        if ctx.interaction:
            await ctx.interaction.followup.send(file=file, ephemeral=True)
        else:
            await ctx.send(file=file)


async def setup(bot: Tux) -> None:
    """Set up the deepfry plugin.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(Deepfry(bot))
