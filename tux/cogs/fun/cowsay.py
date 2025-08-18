import time
import cowsay
from discord.ext import commands
from tux.bot import Tux
from tux.utils.functions import generate_usage

user_cooldowns = {}
cooldown_duration = 180  # 3 minutes

class Cowsay(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.cowsay_command.usage = generate_usage(self.cowsay_command)

    @commands.hybrid_command(
        name="cowsay",
        description="Make the cow say something.",
    )
    @commands.guild_only()
    async def cowsay_command(
        self, 
        ctx: commands.Context[Tux], 
        *, 
        text: str
    ) -> None:
        user_id = ctx.author.id
        now = time.time()

        if user_id in user_cooldowns:
            elapsed = now - user_cooldowns[user_id]
            if elapsed < cooldown_duration:
                remaining = int(cooldown_duration - elapsed)
                await ctx.respond(
                    f"⏳ You're on cooldown! Try again in {remaining} seconds.", 
                    ephemeral=True
                )
                return

        user_cooldowns[user_id] = now
        cow_text = cowsay.get_output_string("cow", text)
        await ctx.send(content=f"```{cow_text}```")

async def setup(bot: Tux) -> None:
    await bot.add_cog(Cowsay(bot))
