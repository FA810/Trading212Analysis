-- schema.sql

CREATE TABLE IF NOT EXISTS stock_transactions (
    id VARCHAR(100) PRIMARY KEY,
    action VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    ticker VARCHAR(50),
    isin VARCHAR(50),
    name VARCHAR(255),
    quantity NUMERIC(20, 10),
    price_per_share NUMERIC(20, 6),
    price_currency VARCHAR(10),
    total_amount NUMERIC(20, 4),
    total_currency VARCHAR(10),
    result NUMERIC(20, 4),
    result_currency VARCHAR(10)
);

CREATE TABLE IF NOT EXISTS cash_flows (
    id VARCHAR(100) PRIMARY KEY,
    action VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    amount NUMERIC(20, 4) NOT NULL,
    currency VARCHAR(10),
    notes TEXT
);