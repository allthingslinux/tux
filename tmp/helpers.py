import traceback

from prisma import Prisma


class PrismaExt(Prisma):
    async def connect_client(self) -> None:
        await self.connect()

    async def where_first(self, table: str, column: str, item: str) -> object:
        try:
            table_obj = getattr(self, table)

            data = await table_obj.find_first(
                where={column: item},
            )

            return data

        except Exception:
            traceback.print_exc()

    async def where_unique(self, table: str, column: str, item: str) -> object:
        try:
            table_obj = getattr(self, table)

            data = await table_obj.find_unique(
                where={column: item},
            )

            return data

        except Exception:
            traceback.print_exc()

    async def where_many(self, table: str, column: str, item: str) -> object:
        """
        You specify the column that you are looking for an use item name
        """

        try:
            table_obj = getattr(self, table)

            data = await table_obj.find_many(
                where={column: item},
            )

            return data

        except Exception:
            traceback.print_exc()

    async def db_data(self, obj_name: str) -> list:
        """
        Returns all items in a table object
        """

        try:
            obj = getattr(self, obj_name)

            items = await obj.find_many()

            return items

        except Exception:
            traceback.print_exc()

    async def sql_executer(self, query: str) -> list:
        try:
            val = await self.query_raw(query)

            return val
        except Exception:
            traceback.print_exc()
