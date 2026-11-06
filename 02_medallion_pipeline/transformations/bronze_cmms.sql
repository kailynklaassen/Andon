-- =============================================================================
-- BRONZE · CMMS (maintenance work orders)
-- =============================================================================
-- Bronze = the raw files, ingested exactly as they arrived, plus lineage columns.
-- * STREAMING TABLE + STREAM read_files(...) = Auto Loader: only NEW files are read
--   on each update, so dropping another day of extracts into the volume is cheap.
-- * No cleaning here on purpose. If silver logic changes we can rebuild from bronze
--   without going back to the source system.
-- * ${raw_path} comes from the pipeline configuration (set from demo_config.yml).
-- =============================================================================

CREATE OR REFRESH STREAMING TABLE bronze_maintenance_work_orders
COMMENT 'Raw CMMS extract: maintenance work orders (Auto Loader from ${raw_path}/cmms/maintenance_work_orders/)'
TBLPROPERTIES ('quality' = 'bronze', 'source_system' = 'cmms')
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
FROM STREAM read_files('${raw_path}/cmms/maintenance_work_orders/', format => 'csv', header => true);
