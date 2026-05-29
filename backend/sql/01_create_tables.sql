-- Amazon Inventory Agent Demo
-- MySQL 8.0
-- Charset: utf8mb4
-- Collation: utf8mb4_unicode_ci

-- DROP 顺序：先删依赖方（逻辑关联），再删基础表
DROP TABLE IF EXISTS inventory_agent_tasks;
DROP TABLE IF EXISTS inventory_agent_analysis;
DROP TABLE IF EXISTS inventory_replenishment_config;
DROP TABLE IF EXISTS amazon_sales_summary;
DROP TABLE IF EXISTS amazon_inventory_snapshot;
DROP TABLE IF EXISTS amazon_product_master;

-- ---------------------------------------------------------------------------
-- 1. 商品主数据表：保存 SKU 维度的商品基础信息
-- ---------------------------------------------------------------------------
CREATE TABLE amazon_product_master (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    seller_id VARCHAR(64) NOT NULL COMMENT '卖家 ID',
    marketplace_id VARCHAR(32) NOT NULL COMMENT '站点 ID',
    marketplace_name VARCHAR(64) NULL COMMENT '站点名称',
    seller_sku VARCHAR(128) NOT NULL COMMENT '卖家 SKU',
    asin VARCHAR(32) NOT NULL COMMENT '亚马逊 ASIN',
    fn_sku VARCHAR(64) NULL COMMENT 'FBA 履约 SKU',
    product_name VARCHAR(512) NULL COMMENT '商品标题',
    brand VARCHAR(128) NULL COMMENT '品牌',
    product_type VARCHAR(64) NULL COMMENT '商品类型',
    category_name VARCHAR(256) NULL COMMENT '类目名称',
    condition_type VARCHAR(32) NULL DEFAULT 'New' COMMENT '商品状况',
    fulfillment_channel VARCHAR(16) NULL DEFAULT 'FBA' COMMENT '履约方式 FBA/FBM',
    listing_status VARCHAR(32) NULL DEFAULT 'Active' COMMENT '刊登状态',
    lifecycle_stage VARCHAR(32) NULL COMMENT '生命周期',
    launch_date DATE NULL COMMENT '上架日期',
    is_deleted TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否已删除',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_seller_marketplace_sku (seller_id, marketplace_id, seller_sku),
    KEY idx_asin (asin),
    KEY idx_seller_id (seller_id),
    KEY idx_listing_status (listing_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='亚马逊商品主数据';

-- ---------------------------------------------------------------------------
-- 2. 库存快照历史表：每次同步保留新记录，同一 SKU 可有多条历史
-- ---------------------------------------------------------------------------
CREATE TABLE amazon_inventory_snapshot (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    seller_id VARCHAR(64) NOT NULL COMMENT '卖家 ID',
    marketplace_id VARCHAR(32) NOT NULL COMMENT '站点 ID',
    seller_sku VARCHAR(128) NOT NULL COMMENT '卖家 SKU',
    asin VARCHAR(32) NOT NULL COMMENT 'ASIN',
    fn_sku VARCHAR(64) NULL COMMENT 'FBA SKU',
    condition_type VARCHAR(32) NULL DEFAULT 'New' COMMENT '商品状况',
    total_quantity INT NOT NULL DEFAULT 0 COMMENT '总库存',
    fulfillable_quantity INT NOT NULL DEFAULT 0 COMMENT '可售库存',
    inbound_working_quantity INT NOT NULL DEFAULT 0 COMMENT '在途-工作中',
    inbound_shipped_quantity INT NOT NULL DEFAULT 0 COMMENT '在途-已发货',
    inbound_receiving_quantity INT NOT NULL DEFAULT 0 COMMENT '在途-接收中',
    total_reserved_quantity INT NOT NULL DEFAULT 0 COMMENT '预留总量',
    pending_customer_order_quantity INT NOT NULL DEFAULT 0 COMMENT '待发货客户订单',
    pending_transshipment_quantity INT NOT NULL DEFAULT 0 COMMENT '待转运',
    fc_processing_quantity INT NOT NULL DEFAULT 0 COMMENT 'FC 处理中',
    total_unfulfillable_quantity INT NOT NULL DEFAULT 0 COMMENT '不可售总量',
    total_researching_quantity INT NOT NULL DEFAULT 0 COMMENT '调查中库存',
    amazon_last_updated_time DATETIME NULL COMMENT '亚马逊侧最后更新时间',
    sync_batch_id VARCHAR(64) NOT NULL COMMENT '同步批次号',
    sync_time DATETIME NOT NULL COMMENT '本次同步时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    PRIMARY KEY (id),
    KEY idx_sku_sync (seller_id, marketplace_id, seller_sku, sync_time),
    KEY idx_sync_batch (sync_batch_id),
    KEY idx_seller_marketplace (seller_id, marketplace_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='FBA 库存快照（保留历史）';

-- ---------------------------------------------------------------------------
-- 3. 销量汇总表：SKU 维度多时间窗口销量，供 Agent 计算日均销量
-- ---------------------------------------------------------------------------
CREATE TABLE amazon_sales_summary (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    seller_id VARCHAR(64) NOT NULL COMMENT '卖家 ID',
    marketplace_id VARCHAR(32) NOT NULL COMMENT '站点 ID',
    seller_sku VARCHAR(128) NOT NULL COMMENT '卖家 SKU',
    asin VARCHAR(32) NOT NULL COMMENT 'ASIN',
    stat_date DATE NOT NULL COMMENT '统计截止日期',
    sales_units_1d INT NOT NULL DEFAULT 0 COMMENT '近 1 天销量',
    sales_units_3d INT NOT NULL DEFAULT 0 COMMENT '近 3 天销量',
    sales_units_7d INT NOT NULL DEFAULT 0 COMMENT '近 7 天销量',
    sales_units_14d INT NOT NULL DEFAULT 0 COMMENT '近 14 天销量',
    sales_units_30d INT NOT NULL DEFAULT 0 COMMENT '近 30 天销量',
    avg_daily_sales_3d DECIMAL(10, 2) NOT NULL DEFAULT 0.00 COMMENT '近 3 天日均销量',
    avg_daily_sales_7d DECIMAL(10, 2) NOT NULL DEFAULT 0.00 COMMENT '近 7 天日均销量',
    avg_daily_sales_30d DECIMAL(10, 2) NOT NULL DEFAULT 0.00 COMMENT '近 30 天日均销量',
    sales_amount_7d DECIMAL(12, 2) NULL DEFAULT 0.00 COMMENT '近 7 天销售额',
    sales_amount_30d DECIMAL(12, 2) NULL DEFAULT 0.00 COMMENT '近 30 天销售额',
    currency VARCHAR(8) NULL DEFAULT 'USD' COMMENT '币种',
    sales_trend VARCHAR(16) NULL COMMENT '销量趋势',
    sales_trend_rate DECIMAL(8, 4) NULL COMMENT '趋势变化率',
    data_source VARCHAR(32) NOT NULL DEFAULT 'excel' COMMENT '数据来源',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_sku_stat_date (seller_id, marketplace_id, seller_sku, stat_date),
    KEY idx_seller_marketplace (seller_id, marketplace_id),
    KEY idx_stat_date (stat_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='销量汇总';

-- ---------------------------------------------------------------------------
-- 4. 补货配置表：SKU 维度补货参数，Agent 断货与补货量判断依据
-- ---------------------------------------------------------------------------
CREATE TABLE inventory_replenishment_config (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    seller_id VARCHAR(64) NOT NULL COMMENT '卖家 ID',
    marketplace_id VARCHAR(32) NOT NULL COMMENT '站点 ID',
    seller_sku VARCHAR(128) NOT NULL COMMENT '卖家 SKU',
    supplier_name VARCHAR(128) NULL COMMENT '供应商名称',
    purchase_lead_time_days INT NOT NULL DEFAULT 0 COMMENT '采购交期（天）',
    domestic_shipping_days INT NOT NULL DEFAULT 0 COMMENT '国内物流天数',
    international_shipping_days INT NOT NULL DEFAULT 0 COMMENT '国际物流天数',
    customs_clearance_days INT NOT NULL DEFAULT 0 COMMENT '清关天数',
    amazon_receiving_days INT NOT NULL DEFAULT 0 COMMENT '亚马逊入仓天数',
    total_replenishment_days INT NOT NULL DEFAULT 0 COMMENT '总补货周期（天）',
    safety_stock_days INT NOT NULL DEFAULT 7 COMMENT '安全库存天数',
    target_stock_days INT NOT NULL DEFAULT 45 COMMENT '目标库存天数',
    max_stock_days INT NOT NULL DEFAULT 90 COMMENT '最大库存天数',
    moq INT NULL DEFAULT 1 COMMENT '最小起订量',
    carton_quantity INT NULL COMMENT '箱规',
    case_pack_quantity INT NULL COMMENT '装箱数',
    preferred_shipping_method VARCHAR(32) NULL COMMENT '首选物流方式',
    reorder_point_days INT NULL COMMENT '再订货点（天）',
    config_status VARCHAR(16) NOT NULL DEFAULT 'complete' COMMENT '配置状态',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_seller_marketplace_sku_config (seller_id, marketplace_id, seller_sku),
    KEY idx_config_status (config_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='补货配置';

-- ---------------------------------------------------------------------------
-- 5. Agent 分析结果表：记录每次分析结果及数据来源 ID，支持批次追溯
-- ---------------------------------------------------------------------------
CREATE TABLE inventory_agent_analysis (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    analysis_batch_id VARCHAR(64) NOT NULL COMMENT '分析批次号',
    seller_id VARCHAR(64) NOT NULL COMMENT '卖家 ID',
    marketplace_id VARCHAR(32) NOT NULL COMMENT '站点 ID',
    seller_sku VARCHAR(128) NOT NULL COMMENT '卖家 SKU',
    asin VARCHAR(32) NOT NULL COMMENT 'ASIN',
    analysis_date DATE NOT NULL COMMENT '分析日期',
    inventory_snapshot_id BIGINT UNSIGNED NULL COMMENT '关联库存快照 ID',
    sales_summary_id BIGINT UNSIGNED NULL COMMENT '关联销量汇总 ID',
    replenishment_config_id BIGINT UNSIGNED NULL COMMENT '关联补货配置 ID',
    fulfillable_quantity INT NOT NULL DEFAULT 0 COMMENT '分析时可售库存',
    total_quantity INT NOT NULL DEFAULT 0 COMMENT '分析时总库存',
    effective_inbound_quantity INT NOT NULL DEFAULT 0 COMMENT '有效在途库存',
    avg_daily_sales_7d DECIMAL(10, 2) NOT NULL DEFAULT 0.00 COMMENT '7 天日均销量',
    avg_daily_sales_30d DECIMAL(10, 2) NOT NULL DEFAULT 0.00 COMMENT '30 天日均销量',
    available_days DECIMAL(10, 2) NULL COMMENT '可售库存可支撑天数',
    total_cover_days DECIMAL(10, 2) NULL COMMENT '总库存覆盖天数',
    inbound_cover_days DECIMAL(10, 2) NULL COMMENT '在途覆盖天数',
    total_replenishment_days INT NULL COMMENT '总补货周期',
    safety_stock_days INT NULL COMMENT '安全库存天数',
    estimated_stockout_date DATE NULL COMMENT '预计断货日期',
    stockout_risk_level VARCHAR(16) NOT NULL DEFAULT 'low' COMMENT '断货风险等级',
    overstock_risk_level VARCHAR(16) NOT NULL DEFAULT 'low' COMMENT '滞销风险等级',
    replenishment_urgency VARCHAR(16) NULL COMMENT '补货紧急度',
    recommended_replenishment_quantity INT NOT NULL DEFAULT 0 COMMENT '建议补货数量',
    recommended_replenishment_date DATE NULL COMMENT '建议补货日期',
    recommended_action VARCHAR(64) NOT NULL DEFAULT 'keep_monitoring' COMMENT '建议动作',
    action_reason TEXT NULL COMMENT '建议原因',
    risk_reason TEXT NULL COMMENT '风险原因',
    need_manual_approval TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否需要人工审批',
    confidence_score DECIMAL(5, 2) NULL COMMENT '置信度分数',
    data_quality_status VARCHAR(32) NOT NULL DEFAULT 'complete' COMMENT '数据质量状态',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id),
    KEY idx_batch_id (analysis_batch_id),
    KEY idx_sku_date (seller_id, marketplace_id, seller_sku, analysis_date),
    KEY idx_stockout_risk (stockout_risk_level),
    KEY idx_overstock_risk (overstock_risk_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='库存 Agent 分析结果';

-- ---------------------------------------------------------------------------
-- 6. 库存运营任务表：Agent 分析后生成的待办，支持状态流转
-- ---------------------------------------------------------------------------
CREATE TABLE inventory_agent_tasks (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    task_id VARCHAR(64) NOT NULL COMMENT '任务唯一标识 UUID',
    analysis_id BIGINT UNSIGNED NOT NULL COMMENT '关联分析记录 ID',
    seller_id VARCHAR(64) NOT NULL COMMENT '卖家 ID',
    marketplace_id VARCHAR(32) NOT NULL COMMENT '站点 ID',
    seller_sku VARCHAR(128) NOT NULL COMMENT '卖家 SKU',
    asin VARCHAR(32) NOT NULL COMMENT 'ASIN',
    task_type VARCHAR(64) NOT NULL COMMENT '任务类型',
    task_title VARCHAR(256) NOT NULL COMMENT '任务标题',
    task_description TEXT NULL COMMENT '任务描述',
    priority VARCHAR(16) NOT NULL DEFAULT 'medium' COMMENT '优先级',
    risk_level VARCHAR(16) NOT NULL COMMENT '关联风险等级',
    suggested_action VARCHAR(64) NOT NULL COMMENT '建议操作',
    action_parameters JSON NULL COMMENT '操作参数',
    expected_impact TEXT NULL COMMENT '预期影响',
    approval_required TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否需要审批',
    task_status VARCHAR(32) NOT NULL DEFAULT 'pending' COMMENT '任务状态',
    assigned_to VARCHAR(64) NULL COMMENT '指派给',
    operator_id VARCHAR(64) NULL COMMENT '操作人 ID',
    operator_note TEXT NULL COMMENT '操作备注',
    resolved_at DATETIME NULL COMMENT '解决时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_task_id (task_id),
    KEY idx_analysis_id (analysis_id),
    KEY idx_task_status (task_status),
    KEY idx_priority_status (priority, task_status),
    KEY idx_sku (seller_id, marketplace_id, seller_sku)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='库存运营任务';

-- 验证命令：
-- SHOW TABLES;
-- DESC amazon_product_master;
-- DESC amazon_inventory_snapshot;
-- DESC amazon_sales_summary;
-- DESC inventory_replenishment_config;
-- DESC inventory_agent_analysis;
-- DESC inventory_agent_tasks;
