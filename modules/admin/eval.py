import ast

import discord
from bot import Tux
from discord.ext import commands
from loguru import logger
from ui.embeds import EmbedCreator
from utils import checks
from utils.config import CONFIG
from utils.functions import generate_usage


def insert_returns(body: list[ast.stmt]) -> None:
    """
    Inserts return statements into the body of the function definition.

    Parameters
    ----------
    body : list[ast.stmt]
        The body of the function definition.

    Returns
    -------
    None
    """

    # Insert return statement if the last expression is a expression statement
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])

    # For if statements, we insert returns into the body and the orelse
    if isinstance(body[-1], ast.If):
        insert_returns(body[-1].body)
        insert_returns(body[-1].orelse)

    # For with blocks, again we insert returns into the body
    if isinstance(body[-1], ast.With):
        insert_returns(body[-1].body)


class Eval(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.eval.usage = generate_usage(self.eval)

    @commands.command(
        name="eval",
        aliases=["e"],
    )
    @commands.guild_only()
    @checks.has_pl(8)  # sysadmin or higher
    async def eval(self, ctx: commands.Context[Tux], *, expression: str) -> None:
        """
        Evaluate a Python expression. (Owner only)

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        expression : str
            The Python expression to evaluate.
        """
        cmd = expression

        # Check if the user is in the discord.py owner_ids list in the bot instance
        if self.bot.owner_ids is None:
            logger.warning("Bot owner IDs are not set.")
            await ctx.send("Bot owner IDs are not set. Better luck next time!", ephemeral=True, delete_after=30)
            return

        if ctx.author.id not in self.bot.owner_ids:
            if not CONFIG.ALLOW_SYSADMINS_EVAL and ctx.author.id in CONFIG.SYSADMIN_IDS:
                logger.warning(
                    f"{ctx.author} tried to run eval but is not the bot owner. (User ID: {ctx.author.id})",
                )
                await ctx.send(
                    "You are not the bot owner and sysadmins are not allowed to use eval. Please contact your bot owner if you need assistance.",
                    delete_after=30,
                )
                return

            logger.warning(
                f"{ctx.author} tried to run eval but is not the bot owner or sysadmin. (User ID: {ctx.author.id})",
            )
            await ctx.send(
                "You are not the bot owner. Better luck next time! (hint: if you are looking for the regular run command its $run)",
                delete_after=30,
            )
            return

        try:
            # Evaluate the expression
            fn_name = "_eval_expr"
            cmd = cmd.strip("` ")

            # Add a layer of indentation
            cmd = "\n".join(f"    {i}" for i in cmd.splitlines())

            # Wrap in async def body
            body = f"async def {fn_name}():\n{cmd}"

            # Parse the body
            parsed = ast.parse(body)

            # Ensure the first statement is a function definition
            if isinstance(parsed.body[0], ast.FunctionDef | ast.AsyncFunctionDef):
                # Access the body of the function definition
                body = parsed.body[0].body
                insert_returns(body)

            env = {
                "bot": ctx.bot,
                "discord": discord,
                "commands": commands,
                "ctx": ctx,
                "__import__": __import__,
            }

            # Execute the code
            exec(compile(parsed, filename="<ast>", mode="exec"), env)

            # Evaluate the function
            evaluated = await eval(f"{fn_name}()", env)

            embed = EmbedCreator.create_embed(
                EmbedCreator.SUCCESS,
                bot=self.bot,
                user_name=ctx.author.name,
                user_display_avatar=ctx.author.display_avatar.url,
                description=f"```py\n{evaluated}```",
            )
            await ctx.reply(embed=embed, ephemeral=True, delete_after=30)
            logger.info(f"{ctx.author} ran an expression: {cmd}")

        except Exception as error:
            embed = EmbedCreator.create_embed(
                EmbedCreator.ERROR,
                bot=self.bot,
                user_name=ctx.author.name,
                user_display_avatar=ctx.author.display_avatar.url,
                description=f"```py\n{error}```",
            )
            await ctx.reply(embed=embed, ephemeral=True, delete_after=30)
            logger.error(f"An error occurred while running an expression: {error}")


async def setup(bot: Tux) -> None:
    await bot.add_cog(Eval(bot))
