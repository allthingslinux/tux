from datetime import datetime
from typing import Any

import discord
import pytz
from discord.ext import commands
from loguru import logger
from reactionmenu import ViewButton, ViewMenu

from tux.wrappers.arch import ArchRepoClient
from tux.wrappers.aur import AURClient, ErrorResult

VOTE_EMOJI_ID = 1278954135374401566
SOURCE_EMOJI_ID = 1278954134300655759
OUT_OF_DATE_EMOJI_ID = 1273494919897681930
REPO_EMOJI_ID = 1278964195550822490
MAINTAINER_EMOJI_ID = 1278978044660289558
LICENSE_EMOJI_ID = 1279086563409531004
VERSION_EMOJI_ID = 1279090224097656923
LATEST_EMOJI_ID = 1279093553674457120
POPULARITY_EMOJI_ID = 1278954133138702378


class Pkg(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_group(
        name="pkg",
        usage="pkg <subcommand>",
    )
    async def pkg(self, ctx: commands.Context[commands.Bot]) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.send_help("pkg")

    @staticmethod
    def format_unix_timestamp(timestamp: int, tz: str = "UTC") -> str:
        dt = datetime.fromtimestamp(timestamp, pytz.timezone(tz))
        return discord.utils.format_dt(dt, style="R")

    @staticmethod
    def format_iso8601_date(date_str: str, tz: str = "UTC") -> str:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00")).astimezone(pytz.timezone(tz))
        return discord.utils.format_dt(dt, style="R")

    async def fetch_aur_package_info(self, term: str) -> list[dict[str, Any]]:
        try:
            result = await AURClient.search(term)
            if isinstance(result, ErrorResult):
                return []
            return [pkg.model_dump() for pkg in result.results]
        except Exception as e:
            logger.error(e)
            return []

    async def fetch_arch_package_info(self, term: str) -> list[dict[str, Any]]:
        try:
            pkg_search_result = await ArchRepoClient.search_package(term) or await ArchRepoClient.search_package(
                term,
                "any",
            )
            return [pkg_search_result.model_dump()] if pkg_search_result else []
        except Exception as e:
            logger.error(e)
            return []

    def build_embed(self, pkg_detail: dict[str, Any], repo: str) -> discord.Embed:
        vote_emoji = self.bot.get_emoji(VOTE_EMOJI_ID)
        source_emoji = self.bot.get_emoji(SOURCE_EMOJI_ID)
        out_of_date_emoji = self.bot.get_emoji(OUT_OF_DATE_EMOJI_ID)
        repo_emoji = self.bot.get_emoji(REPO_EMOJI_ID)
        maintainer_emoji = self.bot.get_emoji(MAINTAINER_EMOJI_ID)
        license_emoji = self.bot.get_emoji(LICENSE_EMOJI_ID)
        version_emoji = self.bot.get_emoji(VERSION_EMOJI_ID)
        latest_emoji = self.bot.get_emoji(LATEST_EMOJI_ID)
        popularity_emoji = self.bot.get_emoji(POPULARITY_EMOJI_ID)

        embed = discord.Embed(
            title=pkg_detail.get("Name") or pkg_detail.get("pkgname"),
            description=f"> {pkg_detail.get('Description') or pkg_detail.get('pkgdesc')}",
            color=discord.Color.blue(),
        )

        if repo.lower() == "aur":
            embed = self.add_aur_fields(
                embed,
                pkg_detail,
                repo_emoji,
                source_emoji,
                latest_emoji,
                vote_emoji,
                popularity_emoji,
                out_of_date_emoji,
                version_emoji,
                license_emoji,
                maintainer_emoji,
            )
        else:
            embed = self.add_arch_fields(
                embed,
                pkg_detail,
                repo_emoji,
                source_emoji,
                latest_emoji,
                version_emoji,
                maintainer_emoji,
                license_emoji,
            )

        return embed

    def add_aur_fields(
        self,
        embed: discord.Embed,
        pkg_detail: dict[str, Any],
        repo_emoji: discord.Emoji | None,
        source_emoji: discord.Emoji | None,
        latest_emoji: discord.Emoji | None,
        vote_emoji: discord.Emoji | None,
        popularity_emoji: discord.Emoji | None,
        out_of_date_emoji: discord.Emoji | None,
        version_emoji: discord.Emoji | None,
        license_emoji: discord.Emoji | None,
        maintainer_emoji: discord.Emoji | None,
    ) -> discord.Embed:
        embed.add_field(name=f"{repo_emoji} Repo", value="aur", inline=True)
        embed.add_field(name=f"{source_emoji} Source", value=f"[View]({pkg_detail['URL']})", inline=True)
        embed.add_field(
            name=f"{latest_emoji} Last Updated",
            value=self.format_unix_timestamp(pkg_detail["LastModified"]),
            inline=True,
        )
        embed.add_field(name=f"{vote_emoji} Votes", value=str(pkg_detail["NumVotes"]), inline=True)
        embed.add_field(name=f"{popularity_emoji} Popularity", value=str(pkg_detail["Popularity"]), inline=True)
        embed.add_field(
            name=f"{out_of_date_emoji} Out of Date",
            value="Yes" if pkg_detail["OutOfDate"] else "No",
            inline=True,
        )
        embed.add_field(name=f"{version_emoji} Version", value=pkg_detail["Version"].split("+")[0] + "...", inline=True)
        embed.add_field(name=f"{license_emoji} License", value=", ".join(pkg_detail.get("License", [])), inline=True)

        if maintainers := self.get_maintainers(pkg_detail, "Maintainer", "CoMaintainers"):
            embed.add_field(name=f"{maintainer_emoji} Maintainers", value=", ".join(maintainers), inline=True)

        return embed

    def add_arch_fields(
        self,
        embed: discord.Embed,
        pkg_detail: dict[str, Any],
        repo_emoji: discord.Emoji | None,
        source_emoji: discord.Emoji | None,
        latest_emoji: discord.Emoji | None,
        version_emoji: discord.Emoji | None,
        maintainer_emoji: discord.Emoji | None,
        license_emoji: discord.Emoji | None,
    ) -> discord.Embed:
        embed.add_field(name=f"{repo_emoji} Repo", value=pkg_detail.get("repo"), inline=True)
        embed.add_field(name=f"{source_emoji} Source", value=f"[View]({pkg_detail['url']})", inline=True)
        embed.add_field(
            name=f"{latest_emoji} Last Updated",
            value=self.format_iso8601_date(pkg_detail["last_update"]),
            inline=True,
        )
        embed.add_field(
            name=f"{version_emoji} Version",
            value=f"{pkg_detail['pkgver']}-{pkg_detail['pkgrel']}",
            inline=True,
        )

        if maintainers := self.get_maintainers(pkg_detail, "packager", "maintainers"):
            embed.add_field(name=f"{maintainer_emoji} Maintainers", value=", ".join(maintainers), inline=True)

        embed.add_field(name=f"{license_emoji} License", value=", ".join(pkg_detail.get("licenses", [])), inline=True)

        return embed

    @staticmethod
    def get_maintainers(pkg_detail: dict[str, Any], primary_key: str, secondary_key: str) -> list[str]:
        maintainers: list[str] = []
        if primary := pkg_detail.get(primary_key):
            maintainers.append(primary)
        if secondary := pkg_detail.get(secondary_key):
            maintainers.extend(secondary)
        return list(set(maintainers))

    @pkg.command(
        name="info",
        usage="pkg info [term] [repo]",
    )
    async def info(
        self,
        ctx: commands.Context[commands.Bot],
        term: str,
        repo: str,
    ) -> None:
        if ctx.guild is None:
            await ctx.send("This command can only be used in a server.")
            return

        pkg_detail: dict[str, Any] | None = None

        if repo.lower() == "aur":
            aur_results = await self.fetch_aur_package_info(term)
            if aur_results:
                pkg_detail = aur_results[0]
        elif repo.lower() == "arch":
            arch_results = await self.fetch_arch_package_info(term)
            if arch_results:
                pkg_detail = arch_results[0]
        else:
            await ctx.send("Invalid repo. Use `aur` or `arch`.")
            return

        if not pkg_detail:
            await ctx.send("No results found.")
            return

        embed = self.build_embed(pkg_detail, repo)
        await ctx.send(embed=embed)

    def build_paginated_results(
        self,
        combined_results: list[dict[str, Any]],
        package: str,
    ) -> list[discord.Embed]:
        vote_emoji = self.bot.get_emoji(VOTE_EMOJI_ID)
        source_emoji = self.bot.get_emoji(SOURCE_EMOJI_ID)
        out_of_date_emoji = self.bot.get_emoji(OUT_OF_DATE_EMOJI_ID)
        repo_emoji = self.bot.get_emoji(REPO_EMOJI_ID)
        maintainer_emoji = self.bot.get_emoji(MAINTAINER_EMOJI_ID)

        pages: list[discord.Embed] = []
        embed = discord.Embed(
            title="Package Search Results",
            description=f"Results for '{package}'",
            color=discord.Color.blurple(),
        )

        for pkg in combined_results:
            description = pkg.get("Description") or pkg.get("pkgdesc") or "No description provided"
            votes = pkg.get("NumVotes")
            source_url = pkg.get("URL") or pkg.get("url")
            maintainer = pkg.get("Maintainer") or pkg.get("packager")
            out_of_date = pkg.get("OutOfDate")
            repo = pkg.get("repo") or "Unknown"
            name = pkg.get("Name") or pkg.get("pkgname") or "No Name"

            pkg_description = f"{repo_emoji} **{repo}** | "

            if source_url:
                pkg_description += f"{source_emoji} **[Source]({source_url})**"
            if maintainer and maintainer != "Unknown":
                pkg_description += f" | {maintainer_emoji} {maintainer}"
            if out_of_date:
                pkg_description += f"\n{out_of_date_emoji} **OUT OF DATE**"

            pkg_description += f"\n> {description}"
            if repo == "aur" and votes is not None:
                pkg_description += f" | {vote_emoji} **Votes**: {votes}"
            pkg_description += "\n"

            if len(embed.fields) >= 5:
                pages.append(embed)
                embed = discord.Embed(
                    title="Package Search Results",
                    description=f"Results for '{package}'",
                    color=discord.Color.blurple(),
                )
            embed.add_field(name=name, value=pkg_description, inline=False)
        if embed.fields:
            pages.append(embed)

        return pages

    @pkg.command(
        name="search",
        usage="pkg search <term>",
    )
    async def search_paginated(
        self,
        ctx: commands.Context[commands.Bot],
        term: str,
    ) -> None:
        if ctx.guild is None:
            await ctx.send("This command can only be used in a server.")
            return

        aur_results = await self.fetch_aur_package_info(term)
        arch_results = await self.fetch_arch_package_info(term)

        if combined_results := aur_results + arch_results:
            pages = self.build_paginated_results(combined_results, term)

            menu = ViewMenu(ctx, menu_type=ViewMenu.TypeEmbed)
            for page in pages:
                menu.add_page(page)

            menu.add_button(ViewButton.go_to_first_page())
            menu.add_button(ViewButton.back())
            menu.add_button(ViewButton.next())
            menu.add_button(ViewButton.go_to_last_page())
            menu.add_button(ViewButton.end_session())

            await menu.start()
        else:
            await ctx.send("No packages found.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Pkg(bot))
