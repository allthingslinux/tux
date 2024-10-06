/*
  Warnings:

  - The primary key for the `Levels` table will be changed. If it partially fails, the table could be left without primary key constraint.

*/
-- AlterTable
ALTER TABLE "Levels" DROP CONSTRAINT "Levels_pkey",
ADD CONSTRAINT "Levels_pkey" PRIMARY KEY ("member_id", "guild_id");
