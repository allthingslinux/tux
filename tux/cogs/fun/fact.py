import random

from discord.ext import commands

from tux.utils.embeds import EmbedCreator


class Fact(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.facts = [
            "The Linux kernel has over 36 million lines of code in its Git repository.",
            "The vast majority of the world's supercomputers run on Linux.",
            "Linux 1.0 was launched on September 17, 1991 featuring 176,250 lines of code.",
            "There's an easter egg in `apt` if you enter `apt moo`.",
            "Linus Torvalds was around 22 years old when he started work on the Linux Kernel in 1991. In the same year, he also released prototypes of the kernel publicly.",
            "Linux's 1.0 release was in March 1994.",
            "Less than 1% of the latest kernel release includes code written by Linus Torvalds.",
            "Linux is used by every major space programme in the world.",
            "Approximately 13.3% of the latest Linux kernel is made up of blank lines.",
            "Vim has various easter eggs. A notable one is found by typing :help 42 into the command bar.",
            "Slackware is the oldest active linux distribution being released on the 17th July 1993.",
            "Freax was the original planned name for Linux.",
            "The first GUI that ran on Linux was X Window System. It ran on Linux Kernel version 0.95.",
            "The Linux Kernel was the first OS kernel to support x86-64 in 2001.",
            "Over 14,600 individual developers from over 1,300 different companies have contributed to the kernel.",
            "95% of the Linux kernel is written in the C programming Language. Assembly language is the second most used language for Linux at 2.8%.",
            "The first kernel version - Version 0.01 - contained about 10,000 lines of code.",
            "96.3% of the top 1,000,000 web servers were reported to run on Linux.",
            "In the early 2000s, Steve Jobs, who at the time was the CEO of Apple, offered a job to Linus Torvalds to work on OSX which Torvalds declined.",
        ]

    @commands.hybrid_group(
        name="fact",
        aliases=["facts"],
        usage="fact",
    )
    async def fact(self, ctx: commands.Context[commands.Bot]) -> None:
        embed = EmbedCreator.create_info_embed(
            title="Fun Fact",
            description=random.choice(self.facts),
            ctx=ctx,
        )

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Fact(bot))
