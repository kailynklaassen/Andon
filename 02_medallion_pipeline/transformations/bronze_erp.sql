-- =============================================================================
-- BRONZE · ERP (orders, master data, purchasing)
-- =============================================================================
-- Bronze = the raw files, ingested exactly as they arrived, plus lineage columns.
-- * STREAMING TABLE + STREAM read_files(...) = Auto Loader: only NEW files are read
--   on each update, so dropping another day of extracts into the volume is cheap.
-- * No cleaning here on purpose. If silver logic changes we can rebuild from bronze
--   without going back to the source system.
-- * ${raw_path} comes from the pipeline configuration (set from demo_config.yml).
-- =============================================================================

CREATE OR REFRESH STREAMING TABLE bronze_plants
COMMENT 'Raw ERP extract: plants (Auto Loader from ${raw_path}/erp/plants/)'
TBLPROPERTIES ('quality' = 'bronze', 'source_system' = 'erp')
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
FROM STREAM read_files('${raw_path}/erp/plants/', format => 'csv', header => true);

CREATE OR REFRESH STREAMING TABLE bronze_warehouses
COMMENT 'Raw ERP extract: warehouses (Auto Loader from ${raw_path}/erp/warehouses/)'
TBLPROPERTIES ('quality' = 'bronze', 'source_system' = 'erp')
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
FROM STREAM read_files('${raw_path}/erp/warehouses/', format => 'csv', header => true);

CREATE OR REFRESH STREAMING TABLE bronze_parts
COMMENT 'Raw ERP extract: parts (Auto Loader from ${raw_path}/erp/parts/)'
TBLPROPERTIES ('quality' = 'bronze', 'source_system' = 'erp')
AS SELECT
  *,
  _metadata.file_path         AS _source_file,
  _metadata.file_modification_time AS _source_file_ts,
  current_timestamp()         AS _ingested_at
FROM STREAM read_files('${raw_path}/erp/parts/', format => 'csv', header => true);

CREATE OR REFRESH STREAMING TABLE bronze_suppliers
COMMENT 'Raw ERP extract: suppliers (Auto Loader from ${raw_path}/erp/suppliers/)'
TBLPROPERTIES ('quality' = 'bronze', 'source_system' = 'erp')
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
FROM STREAM read_files('${raw_path}/erp/suppliers/', format => 'csv', header => true);

CREATE OR REFRESH STREAMING TABLE bronze_materials
COMMENT 'Raw ERP extract: materials (Auto Loader from ${raw_path}/erp/materials/)'
TBLPROPERTIES ('quality' = 'bronze', 'source_system' = 'erp')
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
FROM STREAM read_files('${raw_path}/erp/materials/', format => 'csv', header => true);

CREATE OR REFRESH STREAMING TABLE bronze_bill_of_materials
COMMENT 'Raw ERP extract: bill of materials (Auto Loader from ${raw_path}/erp/bill_of_materials/)'
TBLPROPERTIES ('quality' = 'bronze', 'source_system' = 'erp')
AS SELECT
  *,
  _metadata.file_path         AS _source_file,
  _metadata.file_modification_time AS _source_file_ts,
  current_timestamp()         AS _ingested_at
FROM STREAM read_files('${raw_path}/erp/bill_of_materials/', format => 'csv', header => true);

CREATE OR REFRESH STREAMING TABLE bronze_customers
COMMENT 'Raw ERP extract: customers (Auto Loader from ${raw_path}/erp/customers/)'
TBLPROPERTIES ('quality' = 'bronze', 'source_system' = 'erp')
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
FROM STREAM read_files('${raw_path}/erp/customers/', format => 'csv', header => true);

CREATE OR REFRESH STREAMING TABLE bronze_carriers
COMMENT 'Raw ERP extract: carriers (Auto Loader from ${raw_path}/erp/carriers/)'
TBLPROPERTIES ('quality' = 'bronze', 'source_system' = 'erp')
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
FROM STREAM read_files('${raw_path}/erp/carriers/', format => 'csv', header => true);

CREATE OR REFRESH STREAMING TABLE bronze_purchase_orders
COMMENT 'Raw ERP extract: purchase orders (Auto Loader from ${raw_path}/erp/purchase_orders/)'
TBLPROPERTIES ('quality' = 'bronze', 'source_system' = 'erp')
AS SELECT
  *,
  _metadata.file_path         AS _source_file,
  _metadata.file_modification_time AS _source_file_ts,
  current_timestamp()         AS _ingested_at
FROM STREAM read_files('${raw_path}/erp/purchase_orders/', format => 'csv', header => true);

CREATE OR REFRESH STREAMING TABLE bronze_goods_receipts
COMMENT 'Raw ERP extract: goods receipts (Auto Loader from ${raw_path}/erp/goods_receipts/)'
TBLPROPERTIES ('quality' = 'bronze', 'source_system' = 'erp')
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
FROM STREAM read_files('${raw_path}/erp/goods_receipts/', format => 'csv', header => true);

CREATE OR REFRESH STREAMING TABLE bronze_production_orders
COMMENT 'Raw ERP extract: production orders (Auto Loader from ${raw_path}/erp/production_orders/)'
TBLPROPERTIES ('quality' = 'bronze', 'source_system' = 'erp')
AS SELECT
  *,
  _metadata.file_path         AS _source_file,
  _metadata.file_modification_time AS _source_file_ts,
  current_timestamp()         AS _ingested_at
FROM STREAM read_files('${raw_path}/erp/production_orders/', format => 'csv', header => true);

CREATE OR REFRESH STREAMING TABLE bronze_sales_orders
COMMENT 'Raw ERP extract: sales orders (Auto Loader from ${raw_path}/erp/sales_orders/)'
TBLPROPERTIES ('quality' = 'bronze', 'source_system' = 'erp')
AS SELECT
  *,
  _metadata.file_path         AS _source_file,
  _metadata.file_modification_time AS _source_file_ts,
  current_timestamp()         AS _ingested_at
FROM STREAM read_files('${raw_path}/erp/sales_orders/', format => 'csv', header => true);
