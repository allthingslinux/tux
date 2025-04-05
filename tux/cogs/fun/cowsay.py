from textwrap import wrap

from discord.ext import commands

from tux.bot import Tux
from tux.utils.flags import generate_usage


class Cowsay(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.cowsay.usage = generate_usage(self.cowsay)

    async def draw_textbox(self, message: str) -> str:
        message_lines = wrap(message, 40)
        max_line_length = max(len(line) for line in message_lines)
        message_box_lines: list[str] = []
        message_box_lines.append("/" + ("-" * (max_line_length + 2)) + "\\\n")
        for line in message_lines:
            box_line = "| " + line + (" " * (max_line_length - len(line))) + " |\n"
            message_box_lines.append(box_line)
        message_box_lines.append("\\" + ("-" * (max_line_length + 2)) + "/")
        return "".join(message_box_lines)

    @commands.hybrid_group(
        name="cowsay",
        aliases=["cow"],
    )
    @commands.guild_only()
    async def cowsay(self, ctx: commands.Context[Tux], message: str, creature: str = "cow") -> None:
        """
        xkcd related commands.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.
        message : str
            The message to encode
        creature : str
            Which creature to use for the drawing
        """
        creatures = {
            "cow": r"""
    \   ^__^
     \  (oo)\_______
        (__)\       )\/\
            ||----w |
            ||     ||
                """,
            "tux": r"""
    \
     \
         .--.
        |o_o |
        |:_/ |
       //   \ \
      (|     | )
     /'\_   _/`\
     \___)=(___/
                """,
            "puffy": r"""
    \
     \
               |    .
           .   |L  /|
       _ . |\ _| \--+._/| .
      / ||\| Y J  )   / |/| ./
     J  |)'( |        ` F`.'/
   -<|  F         __     .-<
     | /       .-'. `.  /-. L___
     J \      <    \  | | O\|.-'
   _J \  .-    \/ O | | \  |F
  '-F  -<_.     \   .-'  `-' L__
 __J  _   _.     >-'  )._.   |-'
 `-|.'   /_.           \_|   F
   /.-   .                _.<
  /'    /.'             .'  `\
   /L  /'   |/      _.-'-\
  /'J       ___.---'\|
    |\  .--' V  | `. `
    |/`. `-.     `._)
       / .-.\
 VK    \ (  `\
        `.\
            """,
        }

        if creature not in creatures:
            valid_creatures: list[str] = []
            for idx, key in enumerate(creatures.keys()):
                if idx < len(creatures) - 1:
                    valid_creatures.append(f"{key}, ")
                else:
                    valid_creatures.append(f" and {key}")

            await ctx.send(
                f'Error: "{creature}" is not a valid creature! valid creatures are: {"".join(valid_creatures)}',
                ephemeral=True,
            )
            return

        if len(message) > 250:
            await ctx.send(f"Error! Message too long! ({len(message)} > 250)")
            return

        textbox = await self.draw_textbox(message)
        await ctx.send("```" + textbox + creatures[creature] + "```")


async def setup(bot: Tux) -> None:
    await bot.add_cog(Cowsay(bot))
