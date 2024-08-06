import ast

import discord
from discord.ext import commands
from loguru import logger

from tux.utils import checks
from tux.utils.constants import Constants as CONST
from tux.utils.embeds import EmbedCreator


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
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(
        name="eval",
        aliases=["e"],
        usage="$eval [expression]",
    )
    @commands.guild_only()
    @checks.has_pl(9)
    async def eval(self, ctx: commands.Context[commands.Bot], *, cmd: str) -> None:
        """
        Evaluate a Python expression. (Owner only)

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context in which the command is being invoked.
        cmd : str
            The Python expression to evaluate.
        """

        # Check if the user is the bot owner
        if ctx.author.id != CONST.BOT_OWNER_ID:
            logger.warning(
                f"{ctx.author} tried to run eval but is not the bot owner. (Owner ID: {self.bot.owner_id}, User ID: {ctx.author.id})",
            )
            await ctx.send("You are not the bot owner. Better luck next time!", ephemeral=True, delete_after=30)
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

            embed = EmbedCreator.create_success_embed(
                title="Success!",
                description=f"```py\n{evaluated}```",
                ctx=ctx,
            )

            logger.info(f"{ctx.author} ran an expression: {cmd}")

        except Exception as error:
            embed = EmbedCreator.create_error_embed(
                title="Error!",
                description=f"```py\n{error}```",
                ctx=ctx,
            )

            logger.error(f"An error occurred while running an expression: {error}")

        else:
            await ctx.send(embed=embed, ephemeral=True, delete_after=30)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Eval(bot))
