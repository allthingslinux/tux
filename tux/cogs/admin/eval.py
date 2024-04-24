import ast

import discord
from discord.ext import commands
from loguru import logger

from tux.utils.constants import Constants as CONST


def insert_returns(body: list[ast.stmt]) -> None:
    # insert return stmt if the last expression is a expression statement
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])

    # for if statements, we insert returns into the body and the orelse
    if isinstance(body[-1], ast.If):
        insert_returns(body[-1].body)
        insert_returns(body[-1].orelse)

    # for with blocks, again we insert returns into the body
    if isinstance(body[-1], ast.With):
        insert_returns(body[-1].body)


class Eval(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="eval", description="Evaluate a Python expression. (Owner only)")
    async def run(self, ctx: commands.Context[commands.Bot], *, cmd: str) -> None:
        # Check if the user is the bot owner
        if ctx.author.id != CONST.BOT_OWNER_ID:
            logger.warning(
                f"{ctx.author} tried to run eval but is not the bot owner. (Owner ID: {self.bot.owner_id}, User ID: {ctx.author.id})"
            )
            await ctx.send("You are not the bot owner. Better luck next time!")
            return

        try:
            logger.info(f"Running expression: {cmd}")
            # Evaluate the expression
            fn_name = "_eval_expr"

            cmd = cmd.strip("` ")

            # add a layer of indentation
            cmd = "\n".join(f"    {i}" for i in cmd.splitlines())

            # wrap in async def body
            body = f"async def {fn_name}():\n{cmd}"

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
            exec(compile(parsed, filename="<ast>", mode="exec"), env)

            evaluated = await eval(f"{fn_name}()", env)

            # Send the result
            embed = discord.Embed(
                title="Success!", description=f"Result: {evaluated}", color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"An error occurred while running an expression: {e}")
            # If an error occurs, send the error message
            embed = discord.Embed(
                title="Error!", description=f"An error occurred: {e}", color=discord.Color.red()
            )
            await ctx.send(embed=embed)

        logger.info(f"{ctx.author} ran an expression: {cmd}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Eval(bot))
