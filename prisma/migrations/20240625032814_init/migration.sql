-- CreateEnum
CREATE TYPE "CaseType" AS ENUM ('BAN', 'HACK_BAN', 'TEMP_BAN', 'UNBAN', 'KICK', 'TIMEOUT_ADD', 'TIMEOUT_REMOVE', 'WARN');

-- CreateTable
CREATE TABLE "Guild" (
    "guild_id" BIGINT NOT NULL,
    "guild_joined_at" TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Guild_pkey" PRIMARY KEY ("guild_id")
);

-- CreateTable
CREATE TABLE "Case" (
    "case_id" BIGSERIAL NOT NULL,
    "case_type" "CaseType" NOT NULL,
    "case_reason" TEXT NOT NULL,
    "case_moderator_id" BIGINT NOT NULL,
    "case_target_id" BIGINT NOT NULL,
    "case_number" INTEGER,
    "case_created_at" TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP,
    "case_expires_at" TIMESTAMP(3),
    "guild_id" BIGINT NOT NULL,

    CONSTRAINT "Case_pkey" PRIMARY KEY ("case_id")
);

-- CreateTable
CREATE TABLE "Snippet" (
    "snippet_id" BIGSERIAL NOT NULL,
    "snippet_name" TEXT NOT NULL,
    "snippet_content" TEXT NOT NULL,
    "snippet_user_id" BIGINT NOT NULL,
    "snippet_created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "guild_id" BIGINT NOT NULL,

    CONSTRAINT "Snippet_pkey" PRIMARY KEY ("snippet_id")
);

-- CreateTable
CREATE TABLE "Note" (
    "note_id" BIGSERIAL NOT NULL,
    "note_content" TEXT NOT NULL,
    "note_created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "note_moderator_id" BIGINT NOT NULL,
    "note_target_id" BIGINT NOT NULL,
    "note_number" INTEGER,
    "guild_id" BIGINT NOT NULL,

    CONSTRAINT "Note_pkey" PRIMARY KEY ("note_id")
);

-- CreateTable
CREATE TABLE "Reminder" (
    "reminder_id" BIGSERIAL NOT NULL,
    "reminder_content" TEXT NOT NULL,
    "reminder_created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "reminder_expires_at" TIMESTAMP(3) NOT NULL,
    "reminder_channel_id" BIGINT NOT NULL,
    "reminder_user_id" BIGINT NOT NULL,
    "guild_id" BIGINT NOT NULL,

    CONSTRAINT "Reminder_pkey" PRIMARY KEY ("reminder_id")
);

-- CreateIndex
CREATE UNIQUE INDEX "Guild_guild_id_key" ON "Guild"("guild_id");

-- CreateIndex
CREATE INDEX "Case_case_number_guild_id_idx" ON "Case"("case_number", "guild_id");

-- CreateIndex
CREATE UNIQUE INDEX "Case_case_number_guild_id_key" ON "Case"("case_number", "guild_id");

-- CreateIndex
CREATE INDEX "Snippet_snippet_name_guild_id_idx" ON "Snippet"("snippet_name", "guild_id");

-- CreateIndex
CREATE UNIQUE INDEX "Snippet_snippet_name_guild_id_key" ON "Snippet"("snippet_name", "guild_id");

-- CreateIndex
CREATE INDEX "Note_note_number_guild_id_idx" ON "Note"("note_number", "guild_id");

-- CreateIndex
CREATE UNIQUE INDEX "Note_note_number_guild_id_key" ON "Note"("note_number", "guild_id");

-- AddForeignKey
ALTER TABLE "Case" ADD CONSTRAINT "Case_guild_id_fkey" FOREIGN KEY ("guild_id") REFERENCES "Guild"("guild_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Snippet" ADD CONSTRAINT "Snippet_guild_id_fkey" FOREIGN KEY ("guild_id") REFERENCES "Guild"("guild_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Note" ADD CONSTRAINT "Note_guild_id_fkey" FOREIGN KEY ("guild_id") REFERENCES "Guild"("guild_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Reminder" ADD CONSTRAINT "Reminder_guild_id_fkey" FOREIGN KEY ("guild_id") REFERENCES "Guild"("guild_id") ON DELETE RESTRICT ON UPDATE CASCADE;
