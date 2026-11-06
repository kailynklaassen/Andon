-- =============================================================================
-- BRONZE · MES (lines, work centers, shift results, downtime)
-- =============================================================================
-- Bronze = the raw files, ingested exactly as they arrived, plus lineage columns.
-- * STREAMING TABLE + STREAM read_files(...) = Auto Loader: only NEW files are read
--   on each update, so dropping another day of extracts into the volume is cheap.
-- * No cleaning here on purpose. If silver logic changes we can rebuild from bronze
--   without going back to the source system.
-- * ${raw_path} comes from the pipeline configuration (set from demo_config.yml).
-- =============================================================================

CREATE OR REFRESH STREAMING TABLE bronze_production_lines
COMMENT 'Raw MES extract: production lines (Auto Loader from ${raw_path}/mes/production_lines/)'
TBLPROPERTIES ('quality' = 'bronze', 'source_system' = 'mes')
AS SELECT
  *,
  _metadata.file_path         AS _source_file,
  _metadata.file_modification_time AS _source_file_ts,
  current_timestamp()         AS _ingested_at,
  -- app lineage: NULL for source-system rows; set on rows written back from the app (bronze_app_corrections.py)
  CAST(NULL AS BOOLEAN)       AS _altered_in_app,
  CAST(NULL AS STRING)        AS _app_action_id,
  CAST(NULL AS STRING)        AS _app_approved_by,
  CAST(NULL AS TIMESTAMP)     AS _app_approved_ts
FROM STREAM read_files('${raw_path}/mes/production_lines/', format => 'json');

CREATE OR REFRESH STREAMING TABLE bronze_work_centers
COMMENT 'Raw MES extract: work centers (Auto Loader from ${raw_path}/mes/work_centers/)'
TBLPROPERTIES ('quality' = 'bronze', 'source_system' = 'mes')
AS SELECT
  *,
  _metadata.file_path         AS _source_file,
  _metadata.file_modification_time AS _source_file_ts,
  current_timestamp()         AS _ingested_at,
  -- app lineage: NULL for source-system rows; set on rows written back from the app (bronze_app_corrections.py)
  CAST(NULL AS BOOLEAN)       AS _altered_in_app,
  CAST(NULL AS STRING)        AS _app_action_id,
  CAST(NULL AS STRING)        AS _app_approved_by,
  CAST(NULL AS TIMESTAMP)     AS _app_approved_ts
FROM STREAM read_files('${raw_path}/mes/work_centers/', format => 'json');

CREATE OR REFRESH STREAMING TABLE bronze_shift_production
COMMENT 'Raw MES extract: shift production (Auto Loader from ${raw_path}/mes/shift_production/)'
TBLPROPERTIES ('quality' = 'bronze', 'source_system' = 'mes')
AS SELECT
  *,
  _metadata.file_path         AS _source_file,
  _metadata.file_modification_time AS _source_file_ts,
  current_timestamp()         AS _ingested_at
FROM STREAM read_files('${raw_path}/mes/shift_production/', format => 'json');

CREATE OR REFRESH STREAMING TABLE bronze_downtime_events
COMMENT 'Raw MES extract: downtime events (Auto Loader from ${raw_path}/mes/downtime_events/)'
TBLPROPERTIES ('quality' = 'bronze', 'source_system' = 'mes')
AS SELECT
  *,
  _metadata.file_path         AS _source_file,
  _metadata.file_modification_time AS _source_file_ts,
  current_timestamp()         AS _ingested_at
FROM STREAM read_files('${raw_path}/mes/downtime_events/', format => 'json');
