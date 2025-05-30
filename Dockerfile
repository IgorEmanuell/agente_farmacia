# Dockerfile for Farmácia AI Agent

# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (if any are needed later, e.g., for specific libraries)
# RUN apt-get update && apt-get install -y --no-install-recommends some-package && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Create necessary directories if they don't exist (logs, data)
# Ensure the user running the app has permissions
RUN mkdir -p /app/logs /app/data && chown -R nobody:nogroup /app/logs /app/data

# Change to a non-root user
USER nobody

# Expose the port the app runs on
# Default FastAPI port is 8000, matching config.yaml placeholder
EXPOSE 8000

# Define the command to run the application using Uvicorn
# It will look for the 'app' instance in the 'src.main' module
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

