ALTER TABLE "movies" ADD COLUMN "rating_count" integer;--> statement-breakpoint
ALTER TABLE "movies" ADD COLUMN "avg_rating" real;--> statement-breakpoint
CREATE INDEX "movies_rating_count_idx" ON "movies" USING btree ("rating_count");