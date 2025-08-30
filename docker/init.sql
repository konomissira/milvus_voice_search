CREATE TABLE
IF NOT EXISTS calls
(
  call_id        BIGSERIAL PRIMARY KEY,
  external_id    VARCHAR
(64),
  customer_id    VARCHAR
(64),
  started_at     TIMESTAMPTZ,
  duration_sec   INT,
  file_uri       TEXT,
  transcript     TEXT,
  summary        TEXT,
  sentiment      VARCHAR
(16),
  embedding_model_version VARCHAR
(64),
  created_at     TIMESTAMPTZ DEFAULT NOW
()
);
CREATE INDEX
IF NOT EXISTS idx_calls_started_at ON calls
(started_at);
CREATE INDEX
IF NOT EXISTS idx_calls_customer_id ON calls
(customer_id);
DO $$
BEGIN
    IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'uniq_calls_extid_startedat'
  ) THEN
    ALTER TABLE calls
      ADD CONSTRAINT uniq_calls_extid_startedat
      UNIQUE (external_id, started_at);
END
IF;
END $$;
