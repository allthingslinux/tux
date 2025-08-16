from __future__ import annotations

from tux.database.services.database import DatabaseService


class BaseController:
    def __init__(self, db: DatabaseService | None = None):
        self.db = db or DatabaseService()