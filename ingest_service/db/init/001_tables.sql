-- ========== Core entities ==========
CREATE TABLE IF NOT EXISTS device (
  id        INT PRIMARY KEY,
  name      TEXT NOT NULL,
  init_date TIMESTAMPTZ,
  CONSTRAINT uq_device_name UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS firmware_version (
  id      SERIAL PRIMARY KEY,
  current BOOLEAN,
  name    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS record_type (
  id         SERIAL PRIMARY KEY,
  name       TEXT NOT NULL,
  version_id INT REFERENCES firmware_version(id),
  CONSTRAINT uq_record_type_name UNIQUE (name)
);

-- Known generator types (idempotent seed)
INSERT INTO record_type (name) VALUES
  ('platform_extension_ticks'),
  ('platform_extension_mm'),
  ('battery_charge'),
  ('platform_height_mm')
ON CONFLICT (name) DO NOTHING;

-- ========== Ingestion ==========
CREATE TABLE IF NOT EXISTS raw_record (
  id           BIGSERIAL PRIMARY KEY,
  raw_message  JSONB NOT NULL,
  arrival_time TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_raw_arrival ON raw_record(arrival_time);

CREATE TABLE IF NOT EXISTS ingest_error (
  raw_data_id BIGINT PRIMARY KEY REFERENCES raw_record(id),
  error       TEXT NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ========== Facts ==========
CREATE TABLE IF NOT EXISTS processed_record (
  id          BIGSERIAL PRIMARY KEY,
  device_id   INT NOT NULL REFERENCES device(id),
  raw_data_id BIGINT NOT NULL REFERENCES raw_record(id),
  record_time TIMESTAMPTZ NOT NULL,        -- event time from payload
  type        INT NOT NULL REFERENCES record_type(id),
  value       NUMERIC NOT NULL
);

-- Hot-path indexes
CREATE INDEX IF NOT EXISTS idx_proc_device_time ON processed_record(device_id, record_time DESC);
CREATE INDEX IF NOT EXISTS idx_proc_type_time   ON processed_record(type, record_time DESC);
CREATE INDEX IF NOT EXISTS idx_proc_raw_fk      ON processed_record(raw_data_id);

-- Dedupe guards (no extra columns)
-- 1) One processed row per raw line:
CREATE UNIQUE INDEX IF NOT EXISTS uq_processed_by_raw
  ON processed_record(raw_data_id);

-- 2) Optional idempotency across replays/sends of the same event:
CREATE UNIQUE INDEX IF NOT EXISTS uq_processed_event
  ON processed_record(device_id, type, record_time, value);
