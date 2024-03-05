from fastapi import FastAPI
from kafka import KafkaProducer
from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

producer = KafkaProducer(bootstrap_servers=os.environ.get("KAFKA_BROKER_URL", "localhost:9093"))
topic = os.environ.get("KAFKA_TOPIC", "journal")

def publish_message(message):
    producer.send(topic, message.encode())