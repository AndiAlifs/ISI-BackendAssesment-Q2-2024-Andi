package main

import (
	"context"
	"encoding/json"
	"log"
	"os"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"github.com/go-redis/redis/v8"
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

func createJournal(db *gorm.DB, journal *Journal) error {
	result := db.Create(journal)
	if result.Error != nil {
		return result.Error
	}
	return nil
}

func main() {
	db, err := connectToPostgreSQL()
	if err != nil {
		log.Fatal("Error connecting to database:", err)
	}
	err = db.AutoMigrate(&Journal{})
	if err != nil {
		log.Fatal("Error migrating database:", err)
	}

	redisHost := os.Getenv("REDIS_HOST")
	redisPort := os.Getenv("REDIS_PORT")
	redisAddr := redisHost + ":" + redisPort

	var ctx = context.Background()
	var readerClient = redis.NewClient(&redis.Options{
		Addr: redisAddr,
	})

	subscriber := readerClient.Subscribe(ctx, os.Getenv("REDIS_KEY"))
	
	for {
		log.Println("Waiting for message...")
		msg, err := subscriber.ReceiveMessage(ctx)
		if err != nil {
			log.Fatal("Error reading message:", err)
		}
		
		NewJournal := Journal{}
		err = json.Unmarshal([]byte(msg.Payload), &NewJournal)
		if err != nil {
			log.Printf("Received message: %v", string(msg.Payload))
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
