-- Enable pgvector extension (required for vector type)
CREATE EXTENSION IF NOT EXISTS vector;
--> statement-breakpoint
CREATE TABLE "song_vectors" (
	"id" serial PRIMARY KEY NOT NULL,
	"spotify_id" text NOT NULL,
	"embedding" vector(128) NOT NULL,
	"created_at" timestamp DEFAULT now() NOT NULL,
	"updated_at" timestamp DEFAULT now() NOT NULL,
	CONSTRAINT "song_vectors_spotify_id_unique" UNIQUE("spotify_id")
);
--> statement-breakpoint
ALTER TABLE "song_vectors" ADD CONSTRAINT "song_vectors_spotify_id_songs_id_fk" FOREIGN KEY ("spotify_id") REFERENCES "public"."songs"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
CREATE INDEX "song_vectors_embedding_idx" ON "song_vectors" USING hnsw ("embedding" vector_cosine_ops);--> statement-breakpoint
CREATE INDEX "song_vectors_spotify_id_idx" ON "song_vectors" USING btree ("spotify_id");