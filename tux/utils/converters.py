from typing import Any

from discord.ext import commands

from prisma.enums import CaseType


class CaseTypeConverter(commands.Converter[CaseType]):
    async def convert(self, ctx: commands.Context[Any], argument: str) -> CaseType:
        try:
            return CaseType[argument.upper()]
        except KeyError as e:
            msg = f"Invalid CaseType: {argument}"
            raise commands.BadArgument(msg) from e
