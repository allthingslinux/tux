from typing import Any
import discord
from loguru import logger

from tux.database.controllers import DatabaseController
from tux.utils.constants import Constants as CONST
from prisma.models import Case

db_controller = DatabaseController()
