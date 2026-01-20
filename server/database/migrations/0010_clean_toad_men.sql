CREATE TYPE "public"."interaction_type" AS ENUM('view', 'click', 'skip', 'replay', 'feedback');--> statement-breakpoint
ALTER TABLE "content_feedback" ALTER COLUMN "brings_back_memories" DROP NOT NULL;--> statement-breakpoint
ALTER TABLE "content_feedback" ADD COLUMN "interaction_type" "interaction_type" DEFAULT 'feedback' NOT NULL;--> statement-breakpoint
ALTER TABLE "content_feedback" ADD COLUMN "duration_seconds" integer;