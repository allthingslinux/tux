from prisma import Prisma

db = Prisma(log_queries=True, auto_register=True)
