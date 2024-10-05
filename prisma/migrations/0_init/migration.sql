-- CreateEnum
CREATE TYPE "CaseType" AS ENUM ('BAN', 'UNBAN', 'HACKBAN', 'TEMPBAN', 'KICK', 'SNIPPETBAN', 'TIMEOUT', 'UNTIMEOUT', 'WARN', 'JAIL', 'UNJAIL', 'SNIPPETUNBAN', 'UNTEMPBAN', 'POLLBAN', 'POLLUNBAN');

-- CreateTable
CREATE TABLE "Guild" (
    "guild_id" BIGINT NOT NULL,
    "guild_joined_at" TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP,
    "case_count" BIGINT NOT NULL DEFAULT 0,

    CONSTRAINT "Guild_pkey" PRIMARY KEY ("guild_id")
);

-- CreateTable
CREATE TABLE "GuildConfig" (
    "prefix" TEXT,
    "mod_log_id" BIGINT,
    "audit_log_id" BIGINT,
    "join_log_id" BIGINT,
    "private_log_id" BIGINT,
    "report_log_id" BIGINT,
    "dev_log_id" BIGINT,
    "jail_channel_id" BIGINT,
    "general_channel_id" BIGINT,
    "starboard_channel_id" BIGINT,
    "perm_level_0_role_id" BIGINT,
    "perm_level_1_role_id" BIGINT,
    "perm_level_2_role_id" BIGINT,
    "perm_level_3_role_id" BIGINT,
    "perm_level_4_role_id" BIGINT,
    "perm_level_5_role_id" BIGINT,
    "perm_level_6_role_id" BIGINT,
    "perm_level_7_role_id" BIGINT,
    "base_staff_role_id" BIGINT,
    "base_member_role_id" BIGINT,
    "jail_role_id" BIGINT,
    "quarantine_role_id" BIGINT,
    "guild_id" BIGINT NOT NULL,

    CONSTRAINT "GuildConfig_pkey" PRIMARY KEY ("guild_id")
);

-- CreateTable
CREATE TABLE "Case" (
    "case_id" BIGSERIAL NOT NULL,
    "case_status" BOOLEAN DEFAULT true,
    "case_type" "CaseType" NOT NULL,
    "case_reason" TEXT NOT NULL,
    "case_moderator_id" BIGINT NOT NULL,
    "case_user_id" BIGINT NOT NULL,
    "case_user_roles" BIGINT[] DEFAULT ARRAY[]::BIGINT[],
    "case_number" BIGINT,
    "case_created_at" TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP,
    "case_expires_at" TIMESTAMP(3),
    "case_tempban_expired" BOOLEAN DEFAULT false,
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
    "uses" BIGINT NOT NULL DEFAULT 0,
    "locked" BOOLEAN NOT NULL DEFAULT false,

    CONSTRAINT "Snippet_pkey" PRIMARY KEY ("snippet_id")
);

-- CreateTable
CREATE TABLE "Note" (
    "note_id" BIGSERIAL NOT NULL,
    "note_content" TEXT NOT NULL,
    "note_created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "note_moderator_id" BIGINT NOT NULL,
    "note_user_id" BIGINT NOT NULL,
    "note_number" BIGINT,
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
    "reminder_sent" BOOLEAN NOT NULL DEFAULT false,
    "guild_id" BIGINT NOT NULL,

    CONSTRAINT "Reminder_pkey" PRIMARY KEY ("reminder_id")
);

-- CreateTable
CREATE TABLE "AFKModel" (
    "member_id" BIGINT NOT NULL,
    "nickname" TEXT NOT NULL,
    "reason" TEXT NOT NULL,
    "since" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "guild_id" BIGINT NOT NULL,

    CONSTRAINT "AFKModel_pkey" PRIMARY KEY ("member_id")
);

-- CreateTable
CREATE TABLE "Starboard" (
    "guild_id" BIGINT NOT NULL,
    "starboard_channel_id" BIGINT NOT NULL,
    "starboard_emoji" TEXT NOT NULL,
    "starboard_threshold" INTEGER NOT NULL,

    CONSTRAINT "Starboard_pkey" PRIMARY KEY ("guild_id")
);

-- CreateTable
CREATE TABLE "StarboardMessage" (
    "message_id" BIGINT NOT NULL,
    "message_content" TEXT NOT NULL,
    "message_created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "message_expires_at" TIMESTAMP(3) NOT NULL,
    "message_channel_id" BIGINT NOT NULL,
    "message_user_id" BIGINT NOT NULL,
    "message_guild_id" BIGINT NOT NULL,
    "star_count" INTEGER NOT NULL DEFAULT 0,
    "starboard_message_id" BIGINT NOT NULL,

    CONSTRAINT "StarboardMessage_pkey" PRIMARY KEY ("message_id")
);

-- CreateTable
CREATE TABLE "Levels" (
    "member_id" BIGINT NOT NULL,
    "xp" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "level" BIGINT NOT NULL DEFAULT 0,
    "blacklisted" BOOLEAN NOT NULL DEFAULT false,
    "last_message" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "guild_id" BIGINT NOT NULL,

    CONSTRAINT "Levels_pkey" PRIMARY KEY ("member_id")
);

-- CreateIndex
CREATE INDEX "Guild_guild_id_idx" ON "Guild"("guild_id");

-- CreateIndex
CREATE UNIQUE INDEX "GuildConfig_guild_id_key" ON "GuildConfig"("guild_id");

-- CreateIndex
CREATE INDEX "GuildConfig_guild_id_idx" ON "GuildConfig"("guild_id");

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

-- CreateIndex
CREATE INDEX "Reminder_reminder_id_guild_id_idx" ON "Reminder"("reminder_id", "guild_id");

-- CreateIndex
CREATE UNIQUE INDEX "Reminder_reminder_id_guild_id_key" ON "Reminder"("reminder_id", "guild_id");

-- CreateIndex
CREATE INDEX "AFKModel_member_id_idx" ON "AFKModel"("member_id");

-- CreateIndex
CREATE UNIQUE INDEX "AFKModel_member_id_guild_id_key" ON "AFKModel"("member_id", "guild_id");

-- CreateIndex
CREATE UNIQUE INDEX "Starboard_guild_id_key" ON "Starboard"("guild_id");

-- CreateIndex
CREATE INDEX "Starboard_guild_id_idx" ON "Starboard"("guild_id");

-- CreateIndex
CREATE INDEX "StarboardMessage_message_id_message_guild_id_idx" ON "StarboardMessage"("message_id", "message_guild_id");

-- CreateIndex
CREATE UNIQUE INDEX "StarboardMessage_message_id_message_guild_id_key" ON "StarboardMessage"("message_id", "message_guild_id");

-- CreateIndex
CREATE INDEX "Levels_member_id_idx" ON "Levels"("member_id");

-- CreateIndex
CREATE UNIQUE INDEX "Levels_member_id_guild_id_key" ON "Levels"("member_id", "guild_id");

-- AddForeignKey
ALTER TABLE "GuildConfig" ADD CONSTRAINT "GuildConfig_guild_id_fkey" FOREIGN KEY ("guild_id") REFERENCES "Guild"("guild_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Case" ADD CONSTRAINT "Case_guild_id_fkey" FOREIGN KEY ("guild_id") REFERENCES "Guild"("guild_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Snippet" ADD CONSTRAINT "Snippet_guild_id_fkey" FOREIGN KEY ("guild_id") REFERENCES "Guild"("guild_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Note" ADD CONSTRAINT "Note_guild_id_fkey" FOREIGN KEY ("guild_id") REFERENCES "Guild"("guild_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Reminder" ADD CONSTRAINT "Reminder_guild_id_fkey" FOREIGN KEY ("guild_id") REFERENCES "Guild"("guild_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "AFKModel" ADD CONSTRAINT "AFKModel_guild_id_fkey" FOREIGN KEY ("guild_id") REFERENCES "Guild"("guild_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Starboard" ADD CONSTRAINT "Starboard_guild_id_fkey" FOREIGN KEY ("guild_id") REFERENCES "Guild"("guild_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "StarboardMessage" ADD CONSTRAINT "StarboardMessage_message_guild_id_fkey" FOREIGN KEY ("message_guild_id") REFERENCES "Guild"("guild_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Levels" ADD CONSTRAINT "Levels_guild_id_fkey" FOREIGN KEY ("guild_id") REFERENCES "Guild"("guild_id") ON DELETE RESTRICT ON UPDATE CASCADE;

