"""SQLite schema DDL for the dogfood beta."""

DDL = """
CREATE TABLE IF NOT EXISTS activity_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_key TEXT NOT NULL UNIQUE,
  source_app TEXT NOT NULL,
  surface TEXT NOT NULL,
  title TEXT NOT NULL,
  started_at TEXT NOT NULL,
  duration_seconds INTEGER NOT NULL,
  url TEXT,
  metadata_json TEXT NOT NULL,
  source_adapter TEXT NOT NULL,
  sample_count INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_activity_events_started
  ON activity_events(started_at);
CREATE TABLE IF NOT EXISTS classified_segments (
  segment_key TEXT PRIMARY KEY,
  date TEXT NOT NULL,
  source_app TEXT NOT NULL,
  surface TEXT NOT NULL,
  title TEXT NOT NULL,
  url TEXT,
  started_at TEXT NOT NULL,
  duration_seconds INTEGER NOT NULL,
  label TEXT NOT NULL,
  confidence REAL NOT NULL,
  reason TEXT NOT NULL,
  sample_count INTEGER NOT NULL,
  corrected_label TEXT,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS corrections (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  segment_key TEXT NOT NULL,
  corrected_label TEXT NOT NULL,
  scope TEXT NOT NULL,
  apply_to_future INTEGER NOT NULL DEFAULT 0,
  app TEXT NOT NULL,
  surface TEXT NOT NULL,
  domain TEXT,
  title_pattern TEXT,
  url_pattern TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_corrections_key
  ON corrections(segment_key, created_at);
CREATE TABLE IF NOT EXISTS daily_intents (
  date TEXT PRIMARY KEY,
  focus_text TEXT NOT NULL,
  avoid_text TEXT NOT NULL,
  note TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS review_checkins (
  date TEXT PRIMARY KEY,
  outcome TEXT NOT NULL,
  reflection_text TEXT,
  next_adjustment TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS focus_rescue_actions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT NOT NULL,
  rescue_key TEXT NOT NULL,
  action TEXT NOT NULL,
  evidence_id TEXT,
  note TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_focus_rescue_actions_key
  ON focus_rescue_actions(date, rescue_key, id);
CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS runtime_status (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
"""
