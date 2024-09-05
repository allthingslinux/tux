import io

import discord
import httpx
from discord import app_commands
from discord.ext import commands
from loguru import logger
from PIL import Image, ImageEnhance, ImageOps

from tux.bot import Tux
from tux.utils.embeds import EmbedCreator


class ImgEffect(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.allowed_mimetypes = [
            "image/jpeg",
            "image/png",
        ]

    imgeffect = app_commands.Group(name="imgeffect", description="Image effects")

    @imgeffect.command(
        name="deepfry",
        description="Deepfry an image",
    )
    async def deepfry(self, interaction: discord.Interaction, image: discord.Attachment) -> None:
        """
        Deepfry an image.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object for the command.
        image : discord.File
            The image to deepfry.
        """

        # check if the image is a image
        logger.info(f"Content type: {image.content_type}, Filename: {image.filename}, URL: {image.url}")

        if image.content_type not in self.allowed_mimetypes:
            logger.error("The file is not a permitted image.")

            embed = EmbedCreator.create_error_embed(
                title="Invalid File",
                description="The file must be an image. Allowed types are PNG, JPEG, and JPG.",
                interaction=interaction,
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # say that the image is being processed
        logger.info("Processing image...")
        await interaction.response.defer(ephemeral=True)

        # open url with PIL
        logger.info("Opening image with PIL and HTTPX...")
        async with httpx.AsyncClient() as client:
            response = await client.get(image.url)

        pil_image = Image.open(io.BytesIO(response.content))
        pil_image = pil_image.convert("RGB")
        logger.info("Image opened with PIL.")

        # resize image to 25% then back to original size
        logger.info("Resizing image...")
        pil_image = pil_image.resize((int(pil_image.width * 0.25), int(pil_image.height * 0.25)))
        logger.info("Image resized.")

        # increase sharpness
        logger.info("Increasing sharpness...")
        pil_image = ImageEnhance.Sharpness(pil_image).enhance(100.0)
        logger.info("Sharpness increased.")

        logger.info("Adjusting color...")
        r = pil_image.split()[0]
        r = ImageEnhance.Contrast(r).enhance(2.0)
        r = ImageEnhance.Brightness(r).enhance(1.5)

        colours = ((254, 0, 2), (255, 255, 15))
        r = ImageOps.colorize(r, colours[0], colours[1])
        pil_image = Image.blend(pil_image, r, 0.75)
        logger.info("Color adjustment complete.")

        # send image
        logger.info("Sending image...")
        pil_image = pil_image.resize((int(pil_image.width * 4), int(pil_image.height * 4)))
        arr = io.BytesIO()
        pil_image.save(arr, format="JPEG", quality=1)
        arr.seek(0)
        file = discord.File(arr, filename="deepfried.jpg")

        await interaction.followup.send(file=file, ephemeral=True)


async def setup(bot: Tux) -> None:
    await bot.add_cog(ImgEffect(bot))
