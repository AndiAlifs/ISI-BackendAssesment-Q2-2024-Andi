from fastapi import FastAPI
from kafka import KafkaProducer

app = FastAPI()
producer = KafkaProducer(bootstrap_servers="localhost:9093")

@app.post("/publish/{topic}")
def publish(topic: str):
    print("Publishing message to topic:", topic)
    message = "Hello, Gaess!"
    print("Message:", message.encode())
    producer.send(topic, message.encode())
    return {"status": "Message published successfully"}