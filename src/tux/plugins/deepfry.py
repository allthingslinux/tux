import io
from typing import Any

import discord
from discord.ext import commands
from loguru import logger
from PIL import Image, ImageEnhance, ImageOps

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.services.http_client import http_client
from tux.ui.embeds import EmbedCreator


class Deepfry(BaseCog):
    """Image deepfrying effects for Discord."""

    ALLOWED_MIMETYPES = ("image/jpeg", "image/png", "image/jpg")

    def __init__(self, bot: Tux) -> None:
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

        # Validate the attachment
        if not self._is_valid_attachment(image):
            await self._send_error_embed(
                ctx,
                "Invalid File",
                "The file must be an image. Allowed types are PNG, JPEG, and JPG.",
            )
            return

        # Extract image URL from the attachment
        image_url = self._extract_image_url(ctx, image)

        # Defer for slash commands
        if ctx.interaction:
            await ctx.interaction.response.defer(ephemeral=True)

        # Process the image
        try:
            pil_image = await self._fetch_image(image_url)
            deepfried_image = self._deepfry_image(pil_image)
            await self._send_image_result(ctx, deepfried_image)
        except Exception as e:
            logger.error(f"Error processing deepfry: {e}")
            await self._send_error_embed(ctx, "Error", "An error occurred while processing the image.")

    def _extract_image_url(self, ctx: commands.Context[Any], image: discord.Attachment) -> str:
        """Extract image URL from the attachment."""
        return image.url

    def _is_valid_attachment(self, attachment: discord.Attachment) -> bool:
        """Check if an attachment is a valid image."""
        return attachment.content_type in self.ALLOWED_MIMETYPES

    async def _fetch_image(self, url: str) -> Image.Image:
        """Fetch and load an image from URL."""
        response = await http_client.get(url)
        return Image.open(io.BytesIO(response.content)).convert("RGB")

    def _deepfry_image(self, image: Image.Image) -> Image.Image:
        """Apply deepfry effects to an image."""
        # Downscale for processing
        image = image.resize((int(image.width * 0.25), int(image.height * 0.25)))
        image = ImageEnhance.Sharpness(image).enhance(100.0)

        # Extract red channel and enhance
        r = image.split()[0]
        r = ImageEnhance.Contrast(r).enhance(2.0)
        r = ImageEnhance.Brightness(r).enhance(1.5)

        # Colorize with deepfry colors
        r = ImageOps.colorize(r, "#fe0002", "#ffff0f")  # (254, 0, 2) and (255, 255, 15)
        image = Image.blend(image, r, 0.75)

        # Upscale back to original size
        return image.resize((int(image.width * 4), int(image.height * 4)))

    async def _send_error_embed(self, ctx: commands.Context[Any], title: str, description: str) -> None:
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

    async def _send_image_result(self, ctx: commands.Context[Any], image: Image.Image) -> None:
        """Send the processed image result."""
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=1)
        buffer.seek(0)

        file = discord.File(buffer, filename="deepfried.jpg")

        if ctx.interaction:
            await ctx.interaction.followup.send(file=file, ephemeral=True)
        else:
            await ctx.send(file=file)


async def setup(bot: Tux) -> None:
    await bot.add_cog(Deepfry(bot))
