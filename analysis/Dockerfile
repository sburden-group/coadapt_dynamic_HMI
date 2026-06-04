# Use an official Python 3.8 runtime as a parent image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (needed for some python packages)
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    python3-distutils \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install the specified packages
RUN pip install --no-cache-dir -r requirements.txt

# This allows VS Code to communicate with the container
EXPOSE 8888

# Keep the container running
CMD ["sleep", "infinity"]