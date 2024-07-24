from prisma import Prisma
from tux.utils.constants import Constants as CONST

db = Prisma(log_queries=CONST.DEBUG, auto_register=True)
