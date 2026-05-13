CREATE DATABASE IF NOT EXISTS rail CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'railapp'@'127.0.0.1' IDENTIFIED BY 'railpass';
CREATE USER IF NOT EXISTS 'stationapp'@'127.0.0.1' IDENTIFIED BY 'stationpass';
GRANT ALL PRIVILEGES ON rail.* TO 'railapp'@'127.0.0.1';
FLUSH PRIVILEGES;

USE rail;

CREATE TABLE IF NOT EXISTS passengers (
    session_id VARCHAR(64) PRIMARY KEY,
    passenger_name VARCHAR(96) NOT NULL,
    trust_state VARCHAR(32) NOT NULL,
    partner_id VARCHAR(64) NOT NULL,
    trust_level JSON NULL,
    issued_at BIGINT NOT NULL,
    completed_at BIGINT NULL
);

CREATE TABLE IF NOT EXISTS partner_trust (
    trust_id VARCHAR(64) PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,
    partner_id VARCHAR(64) NOT NULL,
    station_code VARCHAR(16) NOT NULL,
    trust_level JSON NOT NULL,
    status VARCHAR(24) NOT NULL,
    created_at BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(32) PRIMARY KEY,
    train_id VARCHAR(16) NOT NULL,
    passenger_session VARCHAR(64) NOT NULL,
    passenger_name VARCHAR(96) NOT NULL,
    station_code VARCHAR(16) NOT NULL,
    seat_class VARCHAR(24) NOT NULL,
    status VARCHAR(24) NOT NULL,
    origin_name VARCHAR(96) NOT NULL,
    destination_name VARCHAR(96) NOT NULL,
    depart_time VARCHAR(16) NOT NULL,
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS waitlist_entries (
    order_id VARCHAR(32) PRIMARY KEY,
    train_id VARCHAR(16) NOT NULL,
    station_code VARCHAR(16) NOT NULL,
    seat_class VARCHAR(24) NOT NULL,
    status VARCHAR(24) NOT NULL,
    sampled TINYINT NOT NULL DEFAULT 0,
    sample_origin VARCHAR(64) NOT NULL DEFAULT 'none',
    queue_position INT NOT NULL DEFAULT 0,
    updated_at BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS station_profiles (
    station_code VARCHAR(16) PRIMARY KEY,
    station_name VARCHAR(96) NOT NULL,
    batch_open TINYINT NOT NULL DEFAULT 0,
    renderer_profile VARCHAR(48) NOT NULL DEFAULT 'standard',
    notice_profile VARCHAR(48) NOT NULL DEFAULT 'standard',
    signer_route VARCHAR(48) NOT NULL DEFAULT 'public',
    policy_hint JSON NULL,
    updated_at BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS station_notices (
    slug VARCHAR(32) PRIMARY KEY,
    station_code VARCHAR(16) NOT NULL,
    title VARCHAR(160) NOT NULL,
    body TEXT NOT NULL,
    proxy_hint TEXT NOT NULL,
    created_at BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS ticket_index (
    ticket_no VARCHAR(64) PRIMARY KEY,
    passenger VARCHAR(96) NOT NULL,
    train_id VARCHAR(16) NOT NULL,
    station_code VARCHAR(16) NOT NULL,
    status VARCHAR(24) NOT NULL
);

CREATE TABLE IF NOT EXISTS ticket_adjustments (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ticket_no VARCHAR(96) NOT NULL,
    claim_proof VARCHAR(96) NOT NULL DEFAULT '',
    memo TEXT NOT NULL,
    delta INT NOT NULL,
    created_at BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS station_claim_artifacts (
    order_id VARCHAR(32) PRIMARY KEY,
    station_code VARCHAR(16) NOT NULL,
    train_id VARCHAR(16) NOT NULL,
    ticket_no VARCHAR(96) NOT NULL,
    claim_salt VARCHAR(24) NOT NULL,
    claim_digest VARCHAR(96) NOT NULL,
    issued_at BIGINT NOT NULL,
    expires_at BIGINT NOT NULL,
    UNIQUE KEY uniq_claim_digest (claim_digest)
);

CREATE TABLE IF NOT EXISTS station_rule_applications (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    adjustment_id BIGINT NOT NULL,
    order_id VARCHAR(32) NOT NULL,
    station_code VARCHAR(16) NOT NULL,
    rule_state VARCHAR(24) NOT NULL,
    applied_at BIGINT NOT NULL,
    UNIQUE KEY uniq_adjustment_application (adjustment_id)
);

CREATE TABLE IF NOT EXISTS tariff_exception_claims (
    claim_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_id VARCHAR(32) NOT NULL,
    station_code VARCHAR(16) NOT NULL,
    layout_name VARCHAR(48) NOT NULL,
    cell_name VARCHAR(48) NOT NULL,
    entitlement_code VARCHAR(64) NOT NULL,
    device_ref VARCHAR(64) NOT NULL,
    claim_state VARCHAR(24) NOT NULL,
    updated_at BIGINT NOT NULL,
    UNIQUE KEY uniq_tariff_claim (order_id,station_code,cell_name)
);

CREATE TABLE IF NOT EXISTS bureau_layout_cells (
    station_code VARCHAR(16) NOT NULL,
    layout_name VARCHAR(48) NOT NULL,
    cell_name VARCHAR(48) NOT NULL,
    input_class VARCHAR(48) NOT NULL,
    device_ref VARCHAR(64) NOT NULL,
    enabled TINYINT NOT NULL DEFAULT 1,
    updated_at BIGINT NOT NULL,
    PRIMARY KEY (station_code,layout_name,cell_name)
);

CREATE TABLE IF NOT EXISTS depot_device_routes (
    device_ref VARCHAR(64) PRIMARY KEY,
    station_code VARCHAR(16) NOT NULL,
    device_class VARCHAR(48) NOT NULL,
    codec VARCHAR(48) NOT NULL,
    driver_profile VARCHAR(96) NOT NULL DEFAULT '',
    enabled TINYINT NOT NULL DEFAULT 1,
    updated_at BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS enterprise_accounts (
    account_id VARCHAR(32) PRIMARY KEY,
    company_name VARCHAR(128) NOT NULL,
    station_code VARCHAR(16) NOT NULL,
    route_policy JSON NOT NULL,
    status VARCHAR(24) NOT NULL,
    updated_at BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS enterprise_invoices (
    invoice_id VARCHAR(32) PRIMARY KEY,
    account_id VARCHAR(32) NOT NULL,
    order_id VARCHAR(32) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    dispute_state VARCHAR(32) NOT NULL,
    signer_hint VARCHAR(64) NOT NULL,
    updated_at BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS import_batches (
    import_id VARCHAR(32) PRIMARY KEY,
    station_code VARCHAR(16) NOT NULL,
    adapter VARCHAR(64) NOT NULL,
    target_uri VARCHAR(255) NOT NULL,
    status VARCHAR(32) NOT NULL,
    cached_reply TEXT NOT NULL,
    created_at BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS signer_policies (
    policy_id VARCHAR(32) PRIMARY KEY,
    station_code VARCHAR(16) NOT NULL,
    route_name VARCHAR(48) NOT NULL,
    secret_key VARCHAR(128) NOT NULL,
    render_grant VARCHAR(48) NOT NULL,
    enabled TINYINT NOT NULL DEFAULT 1,
    updated_at BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS receipt_nonces (
    nonce VARCHAR(64) PRIMARY KEY,
    station_code VARCHAR(16) NOT NULL,
    order_id VARCHAR(32) NOT NULL,
    used TINYINT NOT NULL DEFAULT 0,
    expires_at BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS settlement_receipts (
    receipt_id VARCHAR(40) PRIMARY KEY,
    batch_id VARCHAR(32) NOT NULL,
    order_id VARCHAR(32) NOT NULL,
    station_code VARCHAR(16) NOT NULL,
    trust_id VARCHAR(64) NOT NULL,
    template_digest VARCHAR(96) NOT NULL,
    nonce VARCHAR(64) NOT NULL,
    policy_id VARCHAR(32) NOT NULL,
    render_grant VARCHAR(48) NOT NULL,
    signature VARCHAR(128) NOT NULL,
    status VARCHAR(24) NOT NULL,
    created_at BIGINT NOT NULL,
    expires_at BIGINT NOT NULL,
    UNIQUE KEY uniq_batch_receipt (batch_id)
);

CREATE TABLE IF NOT EXISTS render_jobs (
    batch_id VARCHAR(32) PRIMARY KEY,
    receipt_id VARCHAR(40) NULL,
    order_id VARCHAR(32) NOT NULL,
    station_code VARCHAR(16) NOT NULL,
    template_digest VARCHAR(96) NOT NULL,
    template_body TEXT NOT NULL,
    data_json JSON NULL,
    status VARCHAR(24) NOT NULL,
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS render_results (
    batch_id VARCHAR(32) PRIMARY KEY,
    ready TINYINT NOT NULL,
    reasons JSON NOT NULL,
    body MEDIUMTEXT NOT NULL,
    finished_at BIGINT NOT NULL
);

GRANT SELECT ON rail.station_profiles TO 'stationapp'@'127.0.0.1';
GRANT SELECT ON rail.station_notices TO 'stationapp'@'127.0.0.1';
GRANT SELECT ON rail.ticket_index TO 'stationapp'@'127.0.0.1';
GRANT SELECT (order_id) ON rail.waitlist_entries TO 'stationapp'@'127.0.0.1';
GRANT SELECT ON rail.station_claim_artifacts TO 'stationapp'@'127.0.0.1';
GRANT INSERT ON rail.station_notices TO 'stationapp'@'127.0.0.1';
GRANT INSERT (ticket_no,claim_proof,memo,delta,created_at) ON rail.ticket_adjustments TO 'stationapp'@'127.0.0.1';
FLUSH PRIVILEGES;
