import random
import tomllib
from typing import Any

import discord
import httpx
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.bot import Tux
from tux.ui.embeds import EmbedCreator
from tux.utils.config import workspace_root
from tux.utils.functions import generate_usage
from tux.utils.substitutions import handle_substitution


class Fact(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.facts_data: dict[str, dict[str, Any]] = {}
        self._load_facts()
        self.fact.usage = generate_usage(self.fact)

    def _load_facts(self) -> None:
        """Load facts from the facts.toml file."""
        facts_path = workspace_root / "assets" / "data" / "facts.toml"
        try:
            data = tomllib.loads(facts_path.read_text(encoding="utf-8"))
            self.facts_data = data.get("facts", {})
            logger.info(f"Loaded the following fact categories from facts.toml: {list(self.facts_data.keys())}")
        except FileNotFoundError:
            logger.warning(f"Facts file not found at {facts_path}")
            self.facts_data = {}
        except Exception as e:
            logger.error(f"Error loading facts: {e}")
            self.facts_data = {}

    async def _fetch_fact(self, fact_type: str) -> tuple[str, str] | None:
        ft = fact_type.lower()
        # Determine category key
        if ft == "random":
            key = random.choice(list(self.facts_data)) if self.facts_data else None
        elif ft in self.facts_data:
            key = ft
        else:
            key = None
            for k, data in self.facts_data.items():
                if (await handle_substitution(self.bot, data.get("name", k.title()))).lower() == ft:
                    key = k
                    break
        if not key:
            return None
        cfg = self.facts_data[key]
        disp = await handle_substitution(self.bot, cfg.get("name", key.title()))
        # Fetch via API if configured
        if cfg.get("fact_api_url") and cfg.get("fact_api_field"):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(cfg["fact_api_url"])
                    resp.raise_for_status()
                    fact_raw = resp.json().get(cfg["fact_api_field"])
            except Exception:
                fact_raw = None
            fact = await handle_substitution(self.bot, fact_raw or "No fact available.")
        else:
            lst = cfg.get("facts", [])
            fact = await handle_substitution(self.bot, random.choice(lst)) if lst else "No facts available."
        return fact, disp

    async def fact_type_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        choices = [app_commands.Choice(name="Random", value="random")] + [
            app_commands.Choice(name=(await handle_substitution(self.bot, data.get("name", key.title()))), value=key)
            for key, data in self.facts_data.items()
        ]
        if current:
            choices = [c for c in choices if current.lower() in c.name.lower()]
        return choices[:25]

    @commands.hybrid_command(name="fact", aliases=["funfact"])
    @app_commands.describe(fact_type="Select the category of fact to retrieve")
    @app_commands.autocomplete(fact_type=fact_type_autocomplete)
    async def fact(self, ctx: commands.Context[Tux], fact_type: str = "random") -> None:
        """Get a fun fact by category or random."""
        res = await self._fetch_fact(fact_type)
        if res:
            fact, category = res
            embed = EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedCreator.INFO,
                user_name=ctx.author.name,
                user_display_avatar=ctx.author.display_avatar.url,
                title=f"Fun Fact ({category})",
                description=fact,
                custom_author_text="Click here to submit more facts!",
                custom_author_text_url="https://github.com/allthingslinux/tux/blob/main/assets/data/facts.toml",
            )
        else:
            names = [
                await handle_substitution(self.bot, data.get("name", key.title()))
                for key, data in self.facts_data.items()
            ]
            embed = EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedCreator.ERROR,
                user_name=ctx.author.name,
                user_display_avatar=ctx.author.display_avatar.url,
                title="Category Not Found",
                description=f"Invalid category '{fact_type}'. Available: {', '.join(names)}",
            )
        await ctx.send(embed=embed)


async def setup(bot: Tux) -> None:
    await bot.add_cog(Fact(bot))
