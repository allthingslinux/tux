from datetime import datetime

from prisma.enums import CaseType
from prisma.models import Case
from tux.database.client import db


class CaseController:
    def __init__(self):
        self.table = db.case

    async def get_all_cases(self) -> list[Case]:
        return await self.table.find_many()

    async def get_case_by_id(self, case_id: int) -> Case | None:
        return await self.table.find_first(where={"case_id": case_id})

    async def insert_case(
        self,
        guild_id: int,
        case_target_id: int,
        case_moderator_id: int,
        case_type: CaseType,
        case_reason: str,
        case_expires_at: datetime | None = None,
    ) -> Case | None:
        return await self.table.create(
            data={
                "guild_id": guild_id,
                "case_target_id": case_target_id,
                "case_moderator_id": case_moderator_id,
                "case_reason": case_reason,
                "case_type": case_type,
                "case_expires_at": case_expires_at,
            },
        )

    async def delete_case_by_id(self, case_id: int) -> None:
        await self.table.delete(where={"case_id": case_id})

    async def update_case_by_case_number_and_guild_id(
        self,
        case_number: int,
        guild_id: int,
        case_reason: str,
    ) -> Case | None:
        return await self.table.update(
            where={"case_number_guild_id": {"case_number": case_number, "guild_id": guild_id}},
            data={"case_reason": case_reason},
        )

    async def get_cases_by_guild_id(self, guild_id: int) -> list[Case] | None:
        return await self.table.find_many(where={"guild_id": guild_id})

    async def get_cases_by_target_id(self, case_target_id: int) -> list[Case] | None:
        return await self.table.find_many(where={"case_target_id": case_target_id})

    async def get_cases_by_moderator_id(self, case_moderator_id: int) -> list[Case] | None:
        return await self.table.find_many(where={"case_moderator_id": case_moderator_id})

    async def get_cases_by_guild_id_and_target_id(
        self,
        guild_id: int,
        case_target_id: int,
    ) -> list[Case] | None:
        return await self.table.find_many(
            where={"guild_id": guild_id, "case_target_id": case_target_id},
        )

    async def get_cases_by_guild_id_and_moderator_id(
        self,
        guild_id: int,
        case_moderator_id: int,
    ) -> list[Case] | None:
        return await self.table.find_many(
            where={"guild_id": guild_id, "case_moderator_id": case_moderator_id},
        )

    async def get_cases_by_guild_id_and_type(
        self,
        guild_id: int,
        case_type: CaseType,
    ) -> list[Case] | None:
        return await self.table.find_many(where={"guild_id": guild_id, "case_type": case_type})

    async def get_cases_by_guild_id_and_reason(
        self,
        guild_id: int,
        case_reason: str,
    ) -> list[Case] | None:
        return await self.table.find_many(where={"guild_id": guild_id, "case_reason": case_reason})

    async def get_cases_by_guild_id_and_expires_at(
        self,
        guild_id: int,
        case_expires_at: datetime,
    ) -> list[Case] | None:
        return await self.table.find_many(
            where={"guild_id": guild_id, "case_expires_at": case_expires_at},
        )

    async def get_cases_by_guild_id_and_target_id_and_moderator_id(
        self,
        guild_id: int,
        case_target_id: int,
        case_moderator_id: int,
    ) -> list[Case] | None:
        return await self.table.find_many(
            where={
                "guild_id": guild_id,
                "case_target_id": case_target_id,
                "case_moderator_id": case_moderator_id,
            },
        )

    async def get_cases_by_guild_id_and_target_id_and_type(
        self,
        guild_id: int,
        case_target_id: int,
        case_type: CaseType,
    ) -> list[Case] | None:
        return await self.table.find_many(
            where={"guild_id": guild_id, "case_target_id": case_target_id, "case_type": case_type},
        )

    async def get_cases_by_guild_id_and_target_id_and_reason(
        self,
        guild_id: int,
        case_target_id: int,
        case_reason: str,
    ) -> list[Case] | None:
        return await self.table.find_many(
            where={
                "guild_id": guild_id,
                "case_target_id": case_target_id,
                "case_reason": case_reason,
            },
        )

    async def get_cases_by_guild_id_and_target_id_and_expires_at(
        self,
        guild_id: int,
        case_target_id: int,
        case_expires_at: datetime,
    ) -> list[Case] | None:
        return await self.table.find_many(
            where={
                "guild_id": guild_id,
                "case_target_id": case_target_id,
                "case_expires_at": case_expires_at,
            },
        )

    async def get_cases_by_guild_id_and_moderator_id_and_type(
        self,
        guild_id: int,
        case_moderator_id: int,
        case_type: CaseType,
    ) -> list[Case] | None:
        return await self.table.find_many(
            where={
                "guild_id": guild_id,
                "case_moderator_id": case_moderator_id,
                "case_type": case_type,
            },
        )

    async def get_cases_by_guild_id_and_moderator_id_and_reason(
        self,
        guild_id: int,
        case_moderator_id: int,
        case_reason: str,
    ) -> list[Case] | None:
        return await self.table.find_many(
            where={
                "guild_id": guild_id,
                "case_moderator_id": case_moderator_id,
                "case_reason": case_reason,
            },
        )

    async def get_cases_by_guild_id_and_moderator_id_and_expires_at(
        self,
        guild_id: int,
        case_moderator_id: int,
        case_expires_at: datetime,
    ) -> list[Case] | None:
        return await self.table.find_many(
            where={
                "guild_id": guild_id,
                "case_moderator_id": case_moderator_id,
                "case_expires_at": case_expires_at,
            },
        )

    async def get_cases_by_guild_id_and_type_and_reason(
        self,
        guild_id: int,
        case_type: CaseType,
        case_reason: str,
    ) -> list[Case] | None:
        return await self.table.find_many(
            where={"guild_id": guild_id, "case_type": case_type, "case_reason": case_reason},
        )

    async def get_cases_by_guild_id_and_type_and_expires_at(
        self,
        guild_id: int,
        case_type: CaseType,
        case_expires_at: datetime,
    ) -> list[Case] | None:
        return await self.table.find_many(
            where={"guild_id": guild_id, "case_type": case_type, "case_expires_at": case_expires_at},
        )

    async def get_cases_by_guild_id_and_reason_and_expires_at(
        self,
        guild_id: int,
        case_reason: str,
        case_expires_at: datetime,
    ) -> list[Case] | None:
        return await self.table.find_many(
            where={
                "guild_id": guild_id,
                "case_reason": case_reason,
                "case_expires_at": case_expires_at,
            },
        )

    async def get_cases_by_guild_id_and_target_id_and_moderator_id_and_type(
        self,
        guild_id: int,
        case_target_id: int,
        case_moderator_id: int,
        case_type: CaseType,
    ) -> list[Case] | None:
        return await self.table.find_many(
            where={
                "guild_id": guild_id,
                "case_target_id": case_target_id,
                "case_moderator_id": case_moderator_id,
                "case_type": case_type,
            },
        )

    async def get_cases_by_guild_id_and_target_id_and_moderator_id_and_reason(
        self,
        guild_id: int,
        case_target_id: int,
        case_moderator_id: int,
        case_reason: str,
    ) -> list[Case] | None:
        return await self.table.find_many(
            where={
                "guild_id": guild_id,
                "case_target_id": case_target_id,
                "case_moderator_id": case_moderator_id,
                "case_reason": case_reason,
            },
        )

    async def get_cases_by_guild_id_and_target_id_and_moderator_id_and_expires_at(
        self,
        guild_id: int,
        case_target_id: int,
        case_moderator_id: int,
        case_expires_at: datetime,
    ) -> list[Case] | None:
        return await self.table.find_many(
            where={
                "guild_id": guild_id,
                "case_target_id": case_target_id,
                "case_moderator_id": case_moderator_id,
                "case_expires_at": case_expires_at,
            },
        )

    async def get_cases_by_guild_id_and_target_id_and_type_and_reason(
        self,
        guild_id: int,
        case_target_id: int,
        case_type: CaseType,
        case_reason: str,
    ) -> list[Case] | None:
        return await self.table.find_many(
            where={
                "guild_id": guild_id,
                "case_target_id": case_target_id,
                "case_type": case_type,
                "case_reason": case_reason,
            },
        )

    async def get_cases_by_guild_id_and_target_id_and_type_and_expires_at(
        self,
        guild_id: int,
        case_target_id: int,
        case_type: CaseType,
        case_expires_at: datetime,
    ) -> list[Case] | None:
        return await self.table.find_many(
            where={
                "guild_id": guild_id,
                "case_target_id": case_target_id,
                "case_type": case_type,
                "case_expires_at": case_expires_at,
            },
        )

    async def get_cases_by_guild_id_and_target_id_and_reason_and_expires_at(
        self,
        guild_id: int,
        case_target_id: int,
        case_reason: str,
        case_expires_at: datetime,
    ) -> list[Case] | None:
        return await self.table.find_many(
            where={
                "guild_id": guild_id,
                "case_target_id": case_target_id,
                "case_reason": case_reason,
                "case_expires_at": case_expires_at,
            },
        )

    async def get_cases_by_guild_id_and_moderator_id_and_type_and_reason(
        self,
        guild_id: int,
        case_moderator_id: int,
        case_type: CaseType,
        case_reason: str,
    ) -> list[Case] | None:
        return await self.table.find_many(
            where={
                "guild_id": guild_id,
                "case_moderator_id": case_moderator_id,
                "case_type": case_type,
                "case_reason": case_reason,
            },
        )

    async def get_cases_by_guild_id_and_moderator_id_and_type_and_expires_at(
        self,
        guild_id: int,
        case_moderator_id: int,
        case_type: CaseType,
        case_expires_at: datetime,
    ) -> list[Case] | None:
        return await self.table.find_many(
            where={
                "guild_id": guild_id,
                "case_moderator_id": case_moderator_id,
                "case_type": case_type,
                "case_expires_at": case_expires_at,
            },
        )

    async def get_cases_by_guild_id_and_moderator_id_and_reason_and_expires_at(
        self,
        guild_id: int,
        case_moderator_id: int,
        case_reason: str,
        case_expires_at: datetime,
    ) -> list[Case] | None:
        return await self.table.find_many(
            where={
                "guild_id": guild_id,
                "case_moderator_id": case_moderator_id,
                "case_reason": case_reason,
                "case_expires_at": case_expires_at,
            },
        )

    async def get_cases_by_guild_id_and_type_and_reason_and_expires_at(
        self,
        guild_id: int,
        case_type: CaseType,
        case_reason: str,
        case_expires_at: datetime,
    ) -> list[Case] | None:
        return await self.table.find_many(
            where={
                "guild_id": guild_id,
                "case_type": case_type,
                "case_reason": case_reason,
                "case_expires_at": case_expires_at,
            },
        )
