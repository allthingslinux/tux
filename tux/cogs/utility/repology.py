import discord
from discord.ext import commands
from loguru import logger
from reactionmenu import ViewButton, ViewMenu
from repology_client.types import Package

from tux.wrappers.repology import RepologyWrapper


class Repology(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.repology = RepologyWrapper()

    @commands.command(name="repology")
    async def repology_command(self, ctx: commands.Context[commands.Bot], project: str) -> None:
        try:
            packages: set[Package] = await self.repology.get_packages(project)
            logger.info(f"Repology packages for {project}: {packages}")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")
            return

        if not packages:
            await ctx.send("No packages found.")
            return

        pages: list[discord.Embed] = []

        embed = discord.Embed(title=f"Repology packages for {project}")

        for count, package in enumerate(packages, start=1):
            logger.info(f"Package: {package}")
            value = package.visiblename
            if package.version:
                value += f" ({package.version})"
            if package.status:
                value += f" - {package.status}"
            if package.summary:
                value += f"\n> {package.summary}"

            embed.add_field(name=package.repo, value=value, inline=False)

            if count % 10 == 0:
                pages.append(embed)
                embed = discord.Embed(title=f"Repology packages for {project}")

        if embed.fields:
            pages.append(embed)

        await self._send_paginated_response(ctx, pages)

    async def _send_paginated_response(self, ctx: commands.Context[commands.Bot], pages: list[discord.Embed]) -> None:
        if pages:
            menu = ViewMenu(ctx, menu_type=ViewMenu.TypeEmbed)

            for page in pages:
                menu.add_page(page)

            menu.add_button(ViewButton.go_to_first_page())
            menu.add_button(ViewButton.back())
            menu.add_button(ViewButton.next())
            menu.add_button(ViewButton.go_to_last_page())
            menu.add_button(ViewButton.end_session())

            await menu.start()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Repology(bot))
