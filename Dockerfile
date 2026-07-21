# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Flask environment
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Expose application port
EXPOSE 5000

# Start Flask application
CMD ["python", "app.py"]