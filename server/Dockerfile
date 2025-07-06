# Use a slim Python base
FROM python:3.11-slim

# Set environment vars
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create app directory
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN apt-get update && apt-get install -y \
    ffmpeg libsndfile1 && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Use Gunicorn for production
CMD ["gunicorn", "-b", "0.0.0.0:8080", "main:app"]
