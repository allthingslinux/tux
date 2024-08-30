from discord.ext import commands
import discord
from reactionmenu import ViewButton, ViewMenu
from tux.wrappers.aur import AURClient
from tux.wrappers.arch import ArchRepoClient
from typing import List, Dict, Any
from datetime import datetime
import logging

VOTE_EMOJI_ID = 1278954135374401566
SOURCE_EMOJI_ID = 1278954134300655759
OUT_OF_DATE_EMOJI_ID = 1273494919897681930
REPO_EMOJI_ID = 1278964195550822490
MAINTAINER_EMOJI_ID = 1278978044660289558


def flatten_list(nested_list: List[Any]) -> List[Any]:
    """Flatten a possibly nested list."""
    flat_list = []
    for item in nested_list:
        if isinstance(item, list):
            flat_list.extend(flatten_list(item))
        else:
            flat_list.append(item)
    return flat_list


class Pkg(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_group(
        name="pkg",
        usage="pkg <subcommand>",
    )
    async def pkg(self, ctx: commands.Context[commands.Bot]) -> None:
        """
        Package related commands.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context object for the command.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help("pkg")

    async def query_aur(self, package: str) -> List[Dict[str, Any]]:
        """Query the AUR for a package."""
        aur_client = AURClient()
        search_result = await aur_client.search(package)
        if isinstance(search_result, SearchResult):
            results = search_result.results
            for pkg in results:
                pkg.repo = "aur"
            return results
        return []

    async def query_arch_repos(self, package: str) -> List[Dict[str, Any]]:
        """Query the official Arch Linux repositories for a package."""
        arch_client = ArchRepoClient()
        search_result = await arch_client.search_packages(name=package)
        if search_result and search_result.valid:
            results = search_result.results
            for pkg in results:
                pkg.repo = "arch"
            return results
        return []

    def filter_packages(self, packages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out packages containing 'i18n' in their name or description."""
        return [
            pkg
            for pkg in packages
            if "i18n" not in (pkg.get("Name") or pkg.get("pkgname", "")).lower()
            and "i18n" not in (pkg.get("Description") or pkg.get("pkgdesc", "")).lower()
        ]

    def format_unix_timestamp(self, timestamp: int) -> str:
        """Convert a UNIX timestamp to a formatted string."""
        dt = datetime.utcfromtimestamp(timestamp)
        return discord.utils.format_dt(dt, style="R")

    def format_iso8601_date(self, date_str: str) -> str:
        """Convert an ISO 8601 date string to a formatted string."""
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return discord.utils.format_dt(dt, style="f")

    async def log_package_details(self, package: Dict[str, Any]) -> None:
        """Log package details for debugging."""
        logging.info(f"Package Details:\n{package}")

    @pkg.command(
        name="search",
        usage="pkg search <package name>",
        aliases=["s"],
    )
    async def search(self, ctx: commands.Context[commands.Bot], package: str) -> None:
        """
        Search for a package on the Arch User Repository (AUR) and official repositories.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The discord context object.
        package : str
            The name of the package to search for.
        """
        # Get the emojis
        vote_emoji = self.bot.get_emoji(VOTE_EMOJI_ID)
        source_emoji = self.bot.get_emoji(SOURCE_EMOJI_ID)
        out_of_date_emoji = self.bot.get_emoji(OUT_OF_DATE_EMOJI_ID)
        repo_emoji = self.bot.get_emoji(REPO_EMOJI_ID)
        maintainer_emoji = self.bot.get_emoji(MAINTAINER_EMOJI_ID)

        aur_results = await self.query_aur(package)
        arch_results = await self.query_arch_repos(package)

        combined_results = self.filter_packages(flatten_list(aur_results + arch_results))

        if combined_results:
            # Ensure all pkgnames are available
            sorted_results = sorted(
                combined_results,
                key=lambda pkg: (pkg.get("pkgname") or pkg.get("Name", "").lower()) == package.lower(),
                reverse=True,
            )

            pages = []
            embed = discord.Embed(
                title="Package Search Results",
                description=f"Results for '{package}'",
                color=discord.Color.blurple(),
            )

            for pkg in sorted_results:
                # Log package information for debugging
                await self.log_package_details(pkg)

                # Handle missing or None values by skipping the field
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

                if len(embed.fields) < 5:  # To limit 5 packages per embed
                    embed.add_field(name=name, value=pkg_description, inline=False)
                else:
                    pages.append(embed)
                    embed = discord.Embed(
                        title="Package Search Results",
                        description=f"Results for '{package}'",
                        color=discord.Color.blurple(),
                    )
                    embed.add_field(name=name, value=pkg_description, inline=False)

            if embed.fields:
                pages.append(embed)

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

    @pkg.command(name="info", usage="pkg info <package name>", aliases=["i"])
    async def info(self, ctx: commands.Context, package: str) -> None:
        """Get information about a package on the Arch User Repository (AUR) or official repositories."""
        # Get the emojis
        vote_emoji = self.bot.get_emoji(VOTE_EMOJI_ID)
        source_emoji = self.bot.get_emoji(SOURCE_EMOJI_ID)
        out_of_date_emoji = self.bot.get_emoji(OUT_OF_DATE_EMOJI_ID)
        repo_emoji = self.bot.get_emoji(REPO_EMOJI_ID)
        maintainer_emoji = self.bot.get_emoji(MAINTAINER_EMOJI_ID)

        aur_client = AURClient()
        arch_client = ArchRepoClient()

        # Fetch from AUR
        aur_results = await aur_client.get_package_info(package)
        # Fetch from official repos with exact match
        arch_results = await arch_client.search_packages(name=package)

        combined_results = self.filter_packages(flatten_list(aur_results.results + arch_results.results))

        if combined_results:
            pkg = combined_results[0]

            # Exact match logic
            for p in combined_results:
                if (p.get("pkgname") or p.get("Name", "").lower()) == package.lower():
                    pkg = p
                    break

            # Logging for debugging
            logging.info(f"Package: {pkg}")
            logging.info(f"Combined Results: {combined_results}")

            repo = pkg.get("repo") or "Unknown"
            version = f"{pkg.get('Version', pkg.get('pkgver', ''))}-{pkg.get('pkgrel', '')}".strip("-")
            maintainer = pkg.get("Maintainer") or pkg.get("packager")
            description = pkg.get("Description") or pkg.get("pkgdesc") or "No description provided"
            votes = pkg.get("NumVotes")
            source_url = pkg.get("URL") or pkg.get("url")
            out_of_date = pkg.get("OutOfDate")
            first_submitted = pkg.get("FirstSubmitted") or pkg.get("build_date")
            last_modified = pkg.get("LastModified") or pkg.get("last_update")
            licenses = pkg.get("License") or pkg.get("licenses", [])
            groups = pkg.get("Groups") or pkg.get("groups", [])

            if first_submitted:
                if isinstance(first_submitted, int):
                    first_submitted = self.format_unix_timestamp(first_submitted)
                else:
                    first_submitted = self.format_iso8601_date(first_submitted)

            if last_modified:
                if isinstance(last_modified, int):
                    last_modified = self.format_unix_timestamp(last_modified)
                else:
                    last_modified = self.format_iso8601_date(last_modified)

            embed = discord.Embed(
                title=f"{pkg.get('Name', pkg.get('pkgname', 'No Name'))}",
                description=f"{repo_emoji} **{repo}** | ",
                color=discord.Color.blurple(),
            )

            # Conditional field additions
            if source_url:
                embed.description += f"{source_emoji} **[Source]({source_url})**"
            if maintainer and maintainer != "Unknown":
                embed.description += f" | {maintainer_emoji} {maintainer}"
            if out_of_date:
                embed.description += f"\n{out_of_date_emoji} **OUT OF DATE**"
            if repo == "aur" and votes is not None:
                embed.description += f"| {vote_emoji} **Votes**: {votes}"

            embed.description += f"\n> {description}\n"

            # Additional fields
            if version:
                embed.add_field(name="Version", value=version, inline=False)
            if first_submitted:
                embed.add_field(name="First Submitted", value=first_submitted, inline=False)
            if last_modified:
                embed.add_field(name="Last Modified", value=last_modified, inline=False)
            if licenses:
                embed.add_field(name="Licenses", value=", ".join(licenses), inline=False)
            if groups:
                embed.add_field(name="Groups", value=", ".join(groups), inline=False)

            await ctx.send(embed=embed)
        else:
            await ctx.send("No package found.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Pkg(bot))
