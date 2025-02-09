from typing import Any

from discord.ext import commands

from prisma.enums import CaseType


class CaseTypeConverter(commands.Converter[CaseType]):
    async def convert(self, ctx: commands.Context[Any], argument: str) -> CaseType:
        """
        Convert a string to a CaseType enum.

        Parameters
        ----------
        ctx : commands.Context[Any]
            The context to convert the argument to a CaseType enum.
        argument : str
            The argument to convert to a CaseType enum.

        Returns
        -------
        CaseType
            The CaseType enum.
        """

        try:
            return CaseType[argument.upper()]
        except KeyError as e:
            msg = f"Invalid CaseType: {argument}"
            raise commands.BadArgument(msg) from e
