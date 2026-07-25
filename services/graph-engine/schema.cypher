// -------------------------------------------------------------
// Constraints
// -------------------------------------------------------------

CREATE CONSTRAINT unique_account_id IF NOT EXISTS FOR (a:Account) REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT unique_customer_id IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT unique_device_id IF NOT EXISTS FOR (d:Device) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT unique_merchant_id IF NOT EXISTS FOR (m:Merchant) REQUIRE m.id IS UNIQUE;

// -------------------------------------------------------------
// Indexes
// -------------------------------------------------------------

// Used for fast bi-temporal querying and property filtering
CREATE INDEX idx_transaction_amount IF NOT EXISTS FOR ()-[r:TRANSACTED_WITH]-() ON (r.amount);
CREATE INDEX idx_transaction_timestamp IF NOT EXISTS FOR ()-[r:TRANSACTED_WITH]-() ON (r.timestamp);
CREATE INDEX idx_transaction_valid_time IF NOT EXISTS FOR ()-[r:TRANSACTED_WITH]-() ON (r.valid_time);

// -------------------------------------------------------------
// Example Schema Setup Notes
// -------------------------------------------------------------
// Nodes:
// (:Account {id: String, type: String, status: String, creation_date: DateTime})
// (:Customer {id: String, name: String, risk_score: Float})
// (:Device {id: String, ip_address: String, os: String})
// (:Merchant {id: String, category_code: String, risk_level: String})
//
// Edges:
// (:Account)-[:TRANSACTED_WITH {
//      transaction_id: String,
//      amount: Float, 
//      timestamp: DateTime,      // Execution/event time
//      valid_time: DateTime,     // Bi-temporal: when record became valid
//      channel: String,
//      location: String
// }]->(:Account)
//
// (:Customer)-[:OWNS_ACCOUNT]->(:Account)
// (:Account)-[:LOGGED_IN_FROM]->(:Device)
