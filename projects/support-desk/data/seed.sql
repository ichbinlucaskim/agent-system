PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS refunds;
DROP TABLE IF EXISTS tickets;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL
);

CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    status TEXT NOT NULL,
    total_usd REAL NOT NULL,
    delivered_days_ago INTEGER,
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE refunds (
    refund_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT NOT NULL REFERENCES orders(order_id),
    amount_usd REAL NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE tickets (
    ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL,
    order_id TEXT,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

INSERT INTO customers VALUES
    ('C-1', 'Ada Lovelace', 'ada@example.com'),
    ('C-2', 'Grace Hopper', 'grace@example.com'),
    ('C-3', 'Alan Turing', 'alan@example.com');

INSERT INTO orders VALUES
    ('ORD-100', 'C-1', 'delivered', 49.99, 5, 'wireless mouse'),
    ('ORD-200', 'C-1', 'delivered', 120.00, 45, 'mechanical keyboard'),
    ('ORD-300', 'C-2', 'shipped', 80.00, NULL, 'usb hub in transit'),
    ('ORD-400', 'C-3', 'processing', 25.00, NULL, 'cable pack not yet packed');
