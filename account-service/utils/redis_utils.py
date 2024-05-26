from fastapi import FastAPI
import redis
from dotenv import load_dotenv
import os
import logging
from loguru import logger

channel = os.getenv("REDIS_KEY")

r = redis.Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), db=os.getenv("REDIS_DB"))
p = r.pubsub()


def publish_message(message):
    r.publish(channel, message)

def produce_transaction_message(transaksi_record):
    send_msg = str(transaksi_record)
    send_msg = send_msg.replace("\'", "\"")
    send_msg = str(send_msg)
    logger.info(f"Publishing message: {send_msg}")
    publish_message(send_msg)