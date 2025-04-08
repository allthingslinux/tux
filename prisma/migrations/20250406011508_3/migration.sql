/*
  Warnings:

  - You are about to drop the column `timeout` on the `AFKModel` table. All the data in the column will be lost.
  - You are about to drop the column `until` on the `AFKModel` table. All the data in the column will be lost.

*/
-- AlterTable
ALTER TABLE "AFKModel" DROP COLUMN "timeout",
DROP COLUMN "until";

-- CreateTable
CREATE TABLE "SelfTimeoutModel" (
    "member_id" BIGINT NOT NULL,
    "nickname" TEXT NOT NULL,
    "reason" TEXT NOT NULL,
    "since" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "until" TIMESTAMP(3),
    "guild_id" BIGINT NOT NULL,
    "perm_afk" BOOLEAN NOT NULL DEFAULT false,

    CONSTRAINT "SelfTimeoutModel_pkey" PRIMARY KEY ("member_id")
);

-- CreateIndex
CREATE INDEX "SelfTimeoutModel_member_id_idx" ON "SelfTimeoutModel"("member_id");

-- CreateIndex
CREATE UNIQUE INDEX "SelfTimeoutModel_member_id_guild_id_key" ON "SelfTimeoutModel"("member_id", "guild_id");

-- AddForeignKey
ALTER TABLE "SelfTimeoutModel" ADD CONSTRAINT "SelfTimeoutModel_guild_id_fkey" FOREIGN KEY ("guild_id") REFERENCES "Guild"("guild_id") ON DELETE RESTRICT ON UPDATE CASCADE;
