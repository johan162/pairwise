FROM python:3.13-slim

WORKDIR /app

# Install system dependencies if needed
# RUN apt-get update && apt-get install -y ...

# Copy requirements first to leverage cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p data

# Environment variables
ENV FLASK_APP=run.py
ENV TASKS_FILE=data/tasks.csv

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "run.py"]
