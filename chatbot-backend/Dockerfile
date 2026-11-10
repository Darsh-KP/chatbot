FROM python:3.11-slim

# Set/create working directory inside the container
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend source code into the container
COPY src/ ./src/

# Copy LLM's Knowledge corpus into container
COPY data/ ./data/

# Create directory for database
RUN mkdir -p /app/db

# Expose port for application to run
EXPOSE 8000

# Run Uvicorn pointing to the src directory (omit --reload for production)
CMD ["uvicorn", "main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]