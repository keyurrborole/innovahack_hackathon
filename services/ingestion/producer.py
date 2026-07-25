import os
import json
import uuid
import random
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from confluent_kafka import Producer
from faker import Faker
from models import Transaction

load_dotenv()

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC = os.getenv("KAFKA_TRANSACTIONS_TOPIC", "transactions")

fake = Faker('en_IN')

# Seed data for accounts
NUM_NORMAL_ACCOUNTS = 500
normal_accounts = [f"ACC_{i:04d}" for i in range(NUM_NORMAL_ACCOUNTS)]

# Specific actors for fraud scenarios
circular_accounts = [f"CIRC_{i}" for i in range(5)]
structuring_source = "STRC_SRC"
structuring_dest = "STRC_DEST"
mule_accounts = [f"MULE_{i}" for i in range(3)]
mule_master = "MULE_MASTER"

def acked(err, msg):
    """Delivery report handler."""
    if err is not None:
        print(f"Failed to deliver message: {str(err)}")
    else:
        # print(f"Message produced to {msg.topic()} [{msg.partition()}] @ offset {msg.offset()}")
        pass

def generate_normal_transaction(timestamp: datetime) -> Transaction:
    source = random.choice(normal_accounts)
    dest = random.choice(normal_accounts)
    while dest == source:
        dest = random.choice(normal_accounts)
        
    amount = round(random.uniform(10.0, 50000.0), 2)
    return Transaction(
        transaction_id=str(uuid.uuid4()),
        source_account=source,
        destination_account=dest,
        amount=amount,
        timestamp=timestamp,
        channel=random.choice(["UPI", "NEFT", "RTGS", "CARD", "IMPS"]),
        location=fake.city(),
        is_fraud=False,
        fraud_pattern=None
    )

def main():
    try:
        producer = Producer({
            'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
            'client.id': 'python-producer'
        })
    except Exception as e:
        print(f"Error initializing Kafka producer: {e}")
        return

    print("Starting producer to generate synthetic transactions...")
    
    current_time = datetime.now() - timedelta(days=30)
    
    transactions_to_send = []
    
    # Generate 9900 normal transactions spread over 30 days
    for _ in range(9900):
        t = (current_time + timedelta(minutes=random.randint(1, 40000)))
        transactions_to_send.append(generate_normal_transaction(t))
        
    # Plant Circular Flow (A -> B -> C -> D -> E -> A)
    # Give it a specific cluster of time for better visibility
    circ_start = current_time + timedelta(days=15)
    amount = round(random.uniform(500000, 1000000), 2)
    for i in range(5):
        t = circ_start + timedelta(minutes=i*10)
        src = circular_accounts[i]
        dst = circular_accounts[(i + 1) % 5]
        transactions_to_send.append(Transaction(
            transaction_id=str(uuid.uuid4()),
            source_account=src,
            destination_account=dst,
            amount=amount,
            timestamp=t,
            channel="RTGS",
            location="Mumbai",
            is_fraud=True,
            fraud_pattern="Circular Flow"
        ))

    # Plant Structuring (9 transactions just below 10 lakh to same account)
    # Threshold in India for reporting is usually 10 lakh
    struct_start = current_time + timedelta(days=20)
    for i in range(9):
        t = struct_start + timedelta(hours=i*2)
        transactions_to_send.append(Transaction(
            transaction_id=str(uuid.uuid4()),
            source_account=structuring_source,
            destination_account=structuring_dest,
            amount=995000.0, # Just under 10 lakh
            timestamp=t,
            channel="NEFT",
            location="Delhi",
            is_fraud=True,
            fraud_pattern="Structuring"
        ))

    # Plant Mule Network (3 accounts receiving small amounts and combining into one)
    mule_start = current_time + timedelta(days=5)
    # Small deposits into mules
    for mule in mule_accounts:
        for _ in range(5):
            t = mule_start + timedelta(hours=random.randint(1, 24))
            src = random.choice(normal_accounts)
            transactions_to_send.append(Transaction(
                transaction_id=str(uuid.uuid4()),
                source_account=src,
                destination_account=mule,
                amount=round(random.uniform(10000, 40000), 2),
                timestamp=t,
                channel="UPI",
                location="Bangalore",
                is_fraud=True,
                fraud_pattern="Mule Deposit"
            ))
        
    # Mules send sum to Master
    transfer_start = mule_start + timedelta(days=2)
    for i, mule in enumerate(mule_accounts):
        t = transfer_start + timedelta(minutes=i*15)
        transactions_to_send.append(Transaction(
            transaction_id=str(uuid.uuid4()),
            source_account=mule,
            destination_account=mule_master,
            amount=150000.0,
            timestamp=t,
            channel="IMPS",
            location="Bangalore",
            is_fraud=True,
            fraud_pattern="Mule Transfer"
        ))
        
    # Sort chronologically
    transactions_to_send.sort(key=lambda x: x.timestamp)
    
    print(f"Total transactions generated: {len(transactions_to_send)}. Sending to Kafka...")
    
    count = 0
    for tx in transactions_to_send:
        # Pydantic v2 dump
        payload = tx.model_dump_json()
        producer.produce(TOPIC, value=payload.encode('utf-8'), callback=acked)
        producer.poll(0)
        count += 1
        
        if count % 1000 == 0:
            print(f"Sent {count} messages...")
            producer.flush()
            time.sleep(0.1) # Small delay
    
    producer.flush()
    print("All transactions sent successfully.")

if __name__ == "__main__":
    main()
