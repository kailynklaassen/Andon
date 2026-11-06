-- =============================================================================
-- BRONZE · HR (workforce)
-- =============================================================================
-- Bronze = the raw files, ingested exactly as they arrived, plus lineage columns.
-- * STREAMING TABLE + STREAM read_files(...) = Auto Loader: only NEW files are read
--   on each update, so dropping another day of extracts into the volume is cheap.
-- * No cleaning here on purpose. If silver logic changes we can rebuild from bronze
--   without going back to the source system.
-- * ${raw_path} comes from the pipeline configuration (set from demo_config.yml).
-- =============================================================================

CREATE OR REFRESH STREAMING TABLE bronze_employees
COMMENT 'Raw HR extract: employees (Auto Loader from ${raw_path}/hr/employees/)'
TBLPROPERTIES ('quality' = 'bronze', 'source_system' = 'hr')
AS SELECT
  *,
  _metadata.file_path         AS _source_file,
  _metadata.file_modification_time AS _source_file_ts,
  current_timestamp()         AS _ingested_at
FROM STREAM read_files('${raw_path}/hr/employees/', format => 'csv', header => true);
