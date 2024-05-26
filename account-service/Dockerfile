# Use the official Python base image
FROM python:3.11

# Set the working directory inside the container
WORKDIR /app


# Copy the requirements file to the working directory
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install opentelemetry-distro
RUN pip install opentelemetry-exporter-otlp-proto-grpc
RUN opentelemetry-bootstrap -a install

# Copy the rest of the application code to the working directory
COPY . .

# Expose the port on which your FastAPI app will run
EXPOSE 8000

# Start the FastAPI app
CMD ["opentelemetry-instrument", "--traces_exporter", "otlp", "--metrics_exporter", "none", "--logs_exporter", "otlp", "--service_name", "account-service","--exporter_otlp_endpoint", "jaeger:4317", "python", "main.py"]
