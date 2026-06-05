# Step 1: Use the official Python 3.11.15 base image
FROM python:3.11.15-slim

# Step 2: Set the working directory inside the container
WORKDIR /workspace

# Step 3: Install system dependencies (needed for some python packages like 'control')
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Step 4: Copy the requirements file into the container
COPY requirements.txt .

# Step 5: Install the python packages
RUN pip install --no-cache-dir -r requirements.txt

# Step 6: Expose the port for Jupyter (optional, but good practice)
EXPOSE 8888