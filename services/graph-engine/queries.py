"""
Pre-defined Cypher queries for the Detection Engine to execute against Neo4j.
"""

# Query 1: Circular Flow Detection
# Identifies instances where money flows through multiple accounts and returns to the originator.
# E.g A -> B -> C -> D -> A within a short time window.
CIRCULAR_FLOW_QUERY = """
MATCH path = (a:Account)-[r1:TRANSACTED_WITH]->(b:Account)-[r2:TRANSACTED_WITH]->(c:Account)-[r3:TRANSACTED_WITH]->(d:Account)-[r4:TRANSACTED_WITH]->(a:Account)
WHERE 
    // Time constraint - happens sequentially
    r1.timestamp < r2.timestamp 
    AND r2.timestamp < r3.timestamp 
    AND r3.timestamp < r4.timestamp
    // Bound the total time window to 24 hours
    AND duration.between(r1.timestamp, r4.timestamp).hours < 24
    // Amount constraint - the amounts are similar (e.g., within 10% indicating fee subtraction)
    AND abs(r1.amount - r2.amount) / r1.amount < 0.10
    AND abs(r2.amount - r3.amount) / r2.amount < 0.10
    AND abs(r3.amount - r4.amount) / r3.amount < 0.10
RETURN path, [r1.amount, r2.amount, r3.amount, r4.amount] AS amounts
LIMIT 100
"""


# Query 2: Structuring Pattern Detection (Smurfing)
# Identifies multiple transactions just below a reporting threshold (e.g. ₹10 Lakhs in India) 
# to the same destination within a short period.
STRUCTURING_QUERY = """
MATCH (src:Account)-[r:TRANSACTED_WITH]->(dst:Account)
WHERE 
    // Just below 1,000,000 INR
    r.amount > 900000 AND r.amount < 1000000
    // Occurred recently
    AND r.timestamp >= datetime($start_time) 
    AND r.timestamp <= datetime($end_time)
WITH src, dst, count(r) AS tx_count, sum(r.amount) AS total_amount, collect(r) as txs
WHERE tx_count >= 5  // Multiple instances
RETURN src.id as Source, dst.id as Destination, tx_count, total_amount, 
       [t in txs | {id: t.transaction_id, amount: t.amount, time: t.timestamp}] as transactions
ORDER BY total_amount DESC
"""


# Query 3: Dormant Account Activation & Rapid Outflow
# Detects when an account has no activity for a long period, suddenly receives funds,
# and immediately transfers them out.
DORMANT_ACCOUNT_ACTIVATION_QUERY = """
MATCH (src1:Account)-[r_in:TRANSACTED_WITH]->(dormant:Account)-[r_out:TRANSACTED_WITH]->(dst:Account)
WHERE 
    // It's the first inward transaction after a long time (simulated via status or date logic)
    // For this query, we check if the dormant account had no transactions in the 6 months prior to r_in
    NOT EXISTS {
        MATCH (any)-[prior:TRANSACTED_WITH]->(dormant)
        WHERE prior.timestamp < r_in.timestamp 
          AND duration.between(prior.timestamp, r_in.timestamp).months < 6
    }
    // And it immediately sends money out within 24 hours
    AND r_out.timestamp > r_in.timestamp
    AND duration.between(r_in.timestamp, r_out.timestamp).hours < 24
    // Transferring out majority of the funds received (>90%)
    AND r_out.amount >= r_in.amount * 0.90
RETURN dormant.id AS SuspiciousAccount, 
       r_in.amount AS ReceivedAmount, 
       r_out.amount AS SentAmount,
       r_in.timestamp AS ActivationTime
ORDER BY r_in.amount DESC
"""


# Query 4: Mule Network Detection (Fan-in -> Fan-out)
# Identifies multiple distinct accounts sending small amounts to a middle account (mule),
# which then forwards the consolidated large amount to a master account.
MULE_NETWORK_QUERY = """
MATCH (victim:Account)-[r_in:TRANSACTED_WITH]->(mule:Account)-[r_out:TRANSACTED_WITH]->(master:Account)
WITH mule, master, r_out, count(DISTINCT victim) AS distinct_victims, sum(r_in.amount) AS total_in
WHERE 
    distinct_victims >= 3
    // E.g., The mule sends out roughly what it received
    AND abs(total_in - r_out.amount) / total_in < 0.15
RETURN mule.id AS MuleAccount, 
       master.id AS MasterAccount,
       distinct_victims AS NumberOfVictims,
       total_in AS TotalDeposits,
       r_out.amount AS TransferredOut
ORDER BY distinct_victims DESC
"""

# Query 5: Bi-Temporal Transaction Check
# Useful to find retroactively modified or late-arriving records for audit purposes.
BI_TEMPORAL_AUDIT_QUERY = """
MATCH (a:Account)-[r:TRANSACTED_WITH]->(b:Account)
WHERE 
    // Record was valid in system significantly later than the event time
    duration.between(r.timestamp, r.valid_time).hours > 48
RETURN a.id, b.id, r.amount, r.timestamp AS EventTime, r.valid_time AS SystemTime
ORDER BY SystemTime DESC
"""
