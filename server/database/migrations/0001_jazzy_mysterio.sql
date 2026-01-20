CREATE TABLE "movies" (
	"id" integer PRIMARY KEY NOT NULL,
	"title" text NOT NULL,
	"year" integer,
	"genres" jsonb,
	"created_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "songs" (
	"id" text PRIMARY KEY NOT NULL,
	"name" text NOT NULL,
	"album_name" text,
	"artists" jsonb,
	"danceability" real,
	"energy" real,
	"key" integer,
	"loudness" real,
	"mode" integer,
	"speechiness" real,
	"acousticness" real,
	"instrumentalness" real,
	"liveness" real,
	"valence" real,
	"tempo" real,
	"duration_ms" integer,
	"lyrics" text,
	"year" integer,
	"genre" text,
	"popularity" integer,
	"niche_genres" jsonb,
	"created_at" timestamp DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE INDEX "movies_year_idx" ON "movies" USING btree ("year");--> statement-breakpoint
CREATE INDEX "songs_year_idx" ON "songs" USING btree ("year");--> statement-breakpoint
CREATE INDEX "songs_genre_idx" ON "songs" USING btree ("genre");--> statement-breakpoint
CREATE INDEX "songs_popularity_idx" ON "songs" USING btree ("popularity");