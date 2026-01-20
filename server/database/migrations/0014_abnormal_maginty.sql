CREATE TABLE "bandit_models" (
	"model_id" text PRIMARY KEY NOT NULL,
	"model_data" text NOT NULL,
	"n_updates" integer DEFAULT 0,
	"updated_at" timestamp DEFAULT now() NOT NULL
);
