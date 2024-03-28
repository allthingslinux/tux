from datetime import datetime

from tux.database.client import db


async def add_user(
    user_id: int, is_bot: bool, username: str, global_name: str, created_at: datetime
):
    return await db.users.create(
        {
            "user_id": user_id,
            "user_is_bot": is_bot,
            "user_username": username,
            "user_global_name": global_name,
            "user_created_at": created_at,
        }
    )


async def get_user(user_id: int):
    return await db.users.find_first(where={"user_id": user_id})


async def add_moderator(moderator_id: int, role_id: int):
    return await db.moderators.create(
        {
            "moderator_id": moderator_id,
            "role_id": role_id,
        }
    )


async def add_infraction(
    moderator_id: int, user_id: int, type: str, reason: str, expires_at: datetime
):
    return await db.infractions.create(
        {
            "moderator_id": moderator_id,
            "user_id": user_id,
            "infraction_type": type,
            "infraction_reason": reason,
            "infraction_expires_at": expires_at,
        }
    )


async def get_infractions(user_id: int):
    infractions = await db.infractions.find_many(where={"user_id": user_id})
    return infractions


async def add_role(role_id: int, role_name: str):
    return await db.roles.create(
        {
            "role_id": role_id,
            "role_name": role_name,
        }
    )


async def add_user_role(user_id: int, role_id: int):
    return await db.user_roles.create(
        {
            "user_id": user_id,
            "role_id": role_id,
        }
    )
