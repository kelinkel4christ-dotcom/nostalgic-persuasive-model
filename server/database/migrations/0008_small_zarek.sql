CREATE TYPE "public"."experiment_group" AS ENUM('treatment', 'control');--> statement-breakpoint
ALTER TABLE "user_preferences" ALTER COLUMN "birth_year" DROP NOT NULL;--> statement-breakpoint
ALTER TABLE "user_preferences" ADD COLUMN "experiment_group" "experiment_group" DEFAULT 'treatment' NOT NULL;