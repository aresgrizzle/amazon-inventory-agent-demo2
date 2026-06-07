-- Amazon Inventory Agent Demo
-- Migration 02: first batch agent decision fields
-- Safe for existing Railway MySQL data.

DELIMITER //

DROP PROCEDURE IF EXISTS add_column_if_missing//
CREATE PROCEDURE add_column_if_missing(
    IN target_table VARCHAR(64),
    IN target_column VARCHAR(64),
    IN column_definition TEXT
)
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = target_table
          AND COLUMN_NAME = target_column
    ) THEN
        SET @ddl = CONCAT('ALTER TABLE ', target_table, ' ADD COLUMN ', target_column, ' ', column_definition);
        PREPARE stmt FROM @ddl;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END//

DELIMITER ;

-- Product profit fields.
CALL add_column_if_missing('amazon_product_master', 'current_price', 'DECIMAL(10,2) NULL DEFAULT 0.00 COMMENT ''Current selling price''');
CALL add_column_if_missing('amazon_product_master', 'purchase_cost', 'DECIMAL(10,2) NULL DEFAULT 0.00 COMMENT ''Unit purchase cost''');
CALL add_column_if_missing('amazon_product_master', 'landed_cost', 'DECIMAL(10,2) NULL DEFAULT 0.00 COMMENT ''Unit landed cost before platform fees''');
CALL add_column_if_missing('amazon_product_master', 'gross_margin', 'DECIMAL(10,4) NULL DEFAULT 0.0000 COMMENT ''Gross margin ratio''');

-- Sales trend fields. sales_trend and sales_trend_rate already exist in the original schema,
-- but these calls keep the migration safe for older or partial databases.
CALL add_column_if_missing('amazon_sales_summary', 'sales_7d', 'INT NOT NULL DEFAULT 0 COMMENT ''Last 7 days sales units''');
CALL add_column_if_missing('amazon_sales_summary', 'sales_30d', 'INT NOT NULL DEFAULT 0 COMMENT ''Last 30 days sales units''');
CALL add_column_if_missing('amazon_sales_summary', 'sales_trend', 'VARCHAR(32) NULL COMMENT ''Sales trend: rising/stable/declining/no_sales''');
CALL add_column_if_missing('amazon_sales_summary', 'sales_trend_rate', 'DECIMAL(10,4) NULL DEFAULT 0.0000 COMMENT ''Sales trend change ratio''');

-- Replenishment strategy fields. safety_stock_days and moq already exist in the original schema.
CALL add_column_if_missing('inventory_replenishment_config', 'total_replenishment_lead_time_days', 'INT NOT NULL DEFAULT 0 COMMENT ''Total replenishment lead time in days''');
CALL add_column_if_missing('inventory_replenishment_config', 'target_cover_days', 'INT NOT NULL DEFAULT 45 COMMENT ''Target inventory cover days''');
CALL add_column_if_missing('inventory_replenishment_config', 'safety_stock_days', 'INT NOT NULL DEFAULT 7 COMMENT ''Safety stock days''');
CALL add_column_if_missing('inventory_replenishment_config', 'moq', 'INT NULL DEFAULT 1 COMMENT ''Minimum order quantity''');

-- Agent analysis decision outputs.
CALL add_column_if_missing('inventory_agent_analysis', 'stockout_risk_score', 'DECIMAL(10,4) NULL DEFAULT 0.0000 COMMENT ''Numeric stockout risk score''');
CALL add_column_if_missing('inventory_agent_analysis', 'overstock_risk_score', 'DECIMAL(10,4) NULL DEFAULT 0.0000 COMMENT ''Numeric overstock risk score''');
CALL add_column_if_missing('inventory_agent_analysis', 'estimated_lost_revenue', 'DECIMAL(12,2) NULL DEFAULT 0.00 COMMENT ''Estimated revenue loss from stockout''');
CALL add_column_if_missing('inventory_agent_analysis', 'decision_confidence', 'DECIMAL(10,4) NULL DEFAULT 0.0000 COMMENT ''Rule decision confidence score''');

-- Task impact and approval fields.
CALL add_column_if_missing('inventory_agent_tasks', 'problem_type', 'VARCHAR(64) NULL COMMENT ''Problem category for operation workflow''');
CALL add_column_if_missing('inventory_agent_tasks', 'impact_level', 'VARCHAR(32) NULL COMMENT ''Business impact level''');
CALL add_column_if_missing('inventory_agent_tasks', 'estimated_impact_value', 'DECIMAL(12,2) NULL DEFAULT 0.00 COMMENT ''Estimated financial impact value''');
CALL add_column_if_missing('inventory_agent_tasks', 'approval_level', 'VARCHAR(32) NULL DEFAULT ''none'' COMMENT ''Approval level: none/operator/manager/owner''');

DROP PROCEDURE IF EXISTS add_column_if_missing;
