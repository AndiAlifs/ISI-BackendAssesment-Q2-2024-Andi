package main

import (
	"context"
	"encoding/json"
	"log"
	"os"

	"github.com/joho/godotenv"
	"github.com/segmentio/kafka-go"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

type Journal struct {
	TanggalTransaksi string `json:"tanggal_transaksi"`
	NoRekeningDebit  string `json:"no_rekening_debit"`
	NoRekeningKredit string `json:"no_rekening_kredit"`
	NominalDebit     int    `json:"nominal_debit"`
	NominalKredit    int    `json:"nominal_kredit"`
}

func connectToPostgreSQL() (*gorm.DB, error) {
	username := os.Getenv("DB_USERNAME")
	password := os.Getenv("DB_PASSWORD")
	dbname := os.Getenv("DB_NAME")
	host := os.Getenv("DB_HOST")
	port := os.Getenv("DB_PORT")

	dsn := "host=" + host + " user=" + username + " password=" + password + " dbname=" + dbname + " port=" + port + " sslmode=disable TimeZone=Asia/Jakarta"
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		return nil, err
	}

	return db, nil
}

func connectToKafkaReader() (*kafka.Reader, error) {
	brokers := os.Getenv("KAFKA_BROKER_URL")
	topic := os.Getenv("KAFKA_TOPIC")
	groupID := os.Getenv("KAFKA_GROUP_ID")

	config := kafka.ReaderConfig{
		Brokers: []string{brokers},
		Topic:   topic,
		GroupID: groupID,
	}

	reader := kafka.NewReader(config)
	return reader, nil
}

func createJournal(db *gorm.DB, journal *Journal) error {
	result := db.Create(journal)
	if result.Error != nil {
		return result.Error
	}
	return nil
}

func main() {
	err := godotenv.Load()
	if err != nil {
		log.Fatal("Error loading .env file")
	}

	db, err := connectToPostgreSQL()
	if err != nil {
		log.Fatal("Error connecting to database:", err)
	}
	err = db.AutoMigrate(&Journal{})
	if err != nil {
		log.Fatal("Error migrating database:", err)
	}

	reader, err := connectToKafkaReader()
	if err != nil {
		log.Fatal("Error connecting to kafka reader:", err)
	}
	defer reader.Close()

	for {
		msg, err := reader.ReadMessage(context.Background())
		if err != nil {
			log.Fatal("Error reading message:", err)
		}

		NewJournal := Journal{}
		err = json.Unmarshal([]byte(msg.Value), &NewJournal)
		if err != nil {
			log.Printf("Received message: %v", string(msg.Value))
			log.Fatal("Error unmarshalling message:", err)
		}
		log.Printf("Received Journal: %v", NewJournal)

		err = createJournal(db, &NewJournal)
		if err != nil {
			log.Fatal("Error creating journal:", err)
		}
		log.Printf("Journal created: %v", NewJournal)
	}
}
