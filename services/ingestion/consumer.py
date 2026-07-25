import os
import sys
import json
import logging
from dotenv import load_dotenv
from confluent_kafka import Consumer, KafkaError, KafkaException
from pydantic import ValidationError
from models import Transaction

load_dotenv()

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC = os.getenv("KAFKA_TRANSACTIONS_TOPIC", "transactions")
GROUP_ID = os.getenv("KAFKA_CONSUMER_GROUP", "ingestion_consumer_group")

# Configure structured JSON logging
logging.basicConfig(level=logging.INFO, format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}')
logger = logging.getLogger(__name__)

def main():
    try:
        consumer = Consumer({
            'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
            'group.id': GROUP_ID,
            'auto.offset.reset': 'earliest'
        })
    except Exception as e:
        logger.error(json.dumps({"error": f"Failed to initialize consumer: {e}"}))
        sys.exit(1)
        
    consumer.subscribe([TOPIC])
    logger.info(json.dumps({"action": "started_consumer", "topic": TOPIC}))
    
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
                
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    logger.info(json.dumps({"info": f"End of partition reached {msg.topic()} [{msg.partition()}] at offset {msg.offset()}"}))
                elif msg.error():
                    raise KafkaException(msg.error())
            else:
                # Valid message
                payload = msg.value().decode('utf-8')
                try:
                    # Parse using Pydantic
                    tx = Transaction.model_validate_json(payload)
                    
                    if tx.is_fraud:
                        logger.warning(json.dumps({
                            "action": "consumed_fraud_pattern",
                            "pattern": tx.fraud_pattern,
                            "transaction_id": tx.transaction_id,
                            "amount": tx.amount
                        }))
                    else:
                        logger.info(json.dumps({
                            "action": "consumed_transaction",
                            "transaction_id": tx.transaction_id
                        }))
                except ValidationError as e:
                    logger.error(json.dumps({
                        "action": "validation_error",
                        "error": e.errors()
                    }))
    except KeyboardInterrupt:
        logger.info(json.dumps({"action": "stopping_consumer"}))
    finally:
        consumer.close()

if __name__ == "__main__":
    main()
