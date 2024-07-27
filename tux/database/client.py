from prisma import Prisma
from tux.utils.constants import Constants as CONST

if CONST.DEBUG is True:
    db = Prisma(log_queries=True, auto_register=True)
else:
    db = Prisma(log_queries=False, auto_register=True)
