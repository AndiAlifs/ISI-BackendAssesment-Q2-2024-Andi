from fastapi import FastAPI
from kafka import KafkaProducer
from dotenv import load_dotenv
import os
import logging
from loguru import logger

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

producer = KafkaProducer(bootstrap_servers=os.environ.get("KAFKA_BROKER_URL", "localhost:9093"))
topic = os.environ.get("KAFKA_TOPIC", "journal")

def publish_message(message):
    producer.send(topic, message.encode())

def produce_transaction_message(transaksi_record):
    send_msg = str(transaksi_record)
    send_msg = send_msg.replace("\'", "\"")
    logger.info(f"Publishing message: {send_msg}")
    publish_message(send_msg)