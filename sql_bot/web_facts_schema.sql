CREATE TABLE IF NOT EXISTS web_facts (
  id SERIAL PRIMARY KEY,
  question   TEXT NOT NULL,
  answer     TEXT NOT NULL,
  source_url TEXT NOT NULL,
  fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Speed up ILIKE '%...%' searches
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX IF NOT EXISTS web_facts_question_trgm_idx
  ON web_facts USING gin (question gin_trgm_ops);
