# Use a base image
FROM golang:1.20

# Set the working directory inside the container
WORKDIR /app

# Copy the go.mod and go.sum files to the working directory
COPY . ./

# Install the dependencies
RUN go mod download
RUN go mod verify
RUN go mod tidy

# Copy the rest of the application code to the working directory
COPY . ./

# Build the application
RUN go build -o /journal-service

# Start the Go app
CMD [ "/journal-service" ]
