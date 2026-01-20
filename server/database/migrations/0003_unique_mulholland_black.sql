CREATE TYPE "public"."content_type" AS ENUM('song', 'movie');--> statement-breakpoint
CREATE TABLE "content_feedback" (
	"id" text PRIMARY KEY NOT NULL,
	"user_id" text NOT NULL,
	"content_type" "content_type" NOT NULL,
	"content_id" text NOT NULL,
	"brings_back_memories" boolean NOT NULL,
	"created_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "daily_habit_logs" (
	"id" text PRIMARY KEY NOT NULL,
	"user_id" text NOT NULL,
	"date" date NOT NULL,
	"completed" boolean NOT NULL,
	"notes" text,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL,
	CONSTRAINT "daily_habit_logs_user_date_unique" UNIQUE("user_id","date")
);
--> statement-breakpoint
ALTER TABLE "content_feedback" ADD CONSTRAINT "content_feedback_user_id_user_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."user"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "daily_habit_logs" ADD CONSTRAINT "daily_habit_logs_user_id_user_id_fk" FOREIGN KEY ("user_id") REFERENCES "public"."user"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
CREATE INDEX "content_feedback_user_id_idx" ON "content_feedback" USING btree ("user_id");--> statement-breakpoint
CREATE INDEX "content_feedback_content_idx" ON "content_feedback" USING btree ("content_type","content_id");--> statement-breakpoint
CREATE INDEX "daily_habit_logs_user_id_idx" ON "daily_habit_logs" USING btree ("user_id");--> statement-breakpoint
CREATE INDEX "daily_habit_logs_date_idx" ON "daily_habit_logs" USING btree ("date");