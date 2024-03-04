package main

import (
	"context"
	"fmt"
	"log"

	"github.com/segmentio/kafka-go"
)

func main() {
	// Set up Kafka reader configuration
	config := kafka.ReaderConfig{
		Brokers: []string{"localhost:9093"},
		Topic:   "journal",
	}

	// Create Kafka reader
	reader := kafka.NewReader(config)
	defer reader.Close()

	// Start consuming messages from the "journal" topic
	for {
		// Read a message from the topic
		msg, err := reader.ReadMessage(context.Background())
		if err != nil {
			log.Fatal("Error reading message:", err)
		}

		// Process the message
		fmt.Println("Received message:", string(msg.Value))
	}
}
