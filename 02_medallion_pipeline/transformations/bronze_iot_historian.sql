-- =============================================================================
-- BRONZE · IoT historian (machine telemetry)
-- =============================================================================
-- Bronze = the raw files, ingested exactly as they arrived, plus lineage columns.
-- * STREAMING TABLE + STREAM read_files(...) = Auto Loader: only NEW files are read
--   on each update, so dropping another day of extracts into the volume is cheap.
-- * No cleaning here on purpose. If silver logic changes we can rebuild from bronze
--   without going back to the source system.
-- * ${raw_path} comes from the pipeline configuration (set from demo_config.yml).
-- =============================================================================

CREATE OR REFRESH STREAMING TABLE bronze_machine_telemetry
COMMENT 'Raw IOT_HISTORIAN extract: machine telemetry (Auto Loader from ${raw_path}/iot_historian/machine_telemetry/)'
TBLPROPERTIES ('quality' = 'bronze', 'source_system' = 'iot_historian')
AS SELECT
  *,
  _metadata.file_path         AS _source_file,
  _metadata.file_modification_time AS _source_file_ts,
  current_timestamp()         AS _ingested_at
FROM STREAM read_files('${raw_path}/iot_historian/machine_telemetry/', format => 'json');
