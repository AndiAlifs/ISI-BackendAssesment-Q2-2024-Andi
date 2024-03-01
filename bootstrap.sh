#!/bin/bash

# Kafka broker address
KAFKA_BROKER="kafka:9093"

# Topic to create
TOPIC="journal_event"

# Wait for Kafka to be ready
until kafka-topics --bootstrap-server $KAFKA_BROKER --list > /dev/null 2>&1; do
  echo "Waiting for Kafka..."
  sleep 1
done

# Check if the topic exists
if kafka-topics --bootstrap-server $KAFKA_BROKER --list | grep -q "^$TOPIC$"; then
    echo "Topic $TOPIC already exists, skipping creation."
else
    # Create the topic
    kafka-topics --bootstrap-server $KAFKA_BROKER --create --topic $TOPIC --partitions 1 --replication-factor 1
    echo "Topic $TOPIC created."
fi