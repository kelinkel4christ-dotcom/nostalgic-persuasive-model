CREATE TYPE "public"."habit_type" AS ENUM('exercise', 'smoking_cessation');--> statement-breakpoint
CREATE TABLE "user_preferences" (
	"id" text PRIMARY KEY NOT NULL,
	"user_id" text NOT NULL,
	"birth_year" integer NOT NULL,
	"nostalgic_period_start" integer NOT NULL,
	"nostalgic_period_end" integer NOT NULL,
	"habit_type" "habit_type" NOT NULL,
	"selected_movie_ids" jsonb DEFAULT '[]'::jsonb,
	"selected_song_ids" jsonb DEFAULT '[]'::jsonb,
	"research_consent" boolean DEFAULT false NOT NULL,
	"onboarding_completed_at" timestamp,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL,
	CONSTRAINT "user_preferences_user_id_unique" UNIQUE("user_id")
);
--> statement-breakpoint
ALTER TABLE "user_preferences" ADD CONSTRAINT "user_preferences_user_id_user_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."user"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
CREATE INDEX "user_preferences_user_id_idx" ON "user_preferences" USING btree ("user_id");