
# Use a stable and lightweight Python image
FROM python:3.10-slim

# Set working directory inside the container
WORKDIR /app

# Copy all project files into the container
COPY . .

# Install dependencies
pip install -r requirements.txt

# Expose the port your app will run on
EXPOSE 8080

# Start your Flask app using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
