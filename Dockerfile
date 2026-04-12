FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy and install dependencies first (for Docker cache efficiency)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source files from src/ subdirectory into /app
COPY src/models.py .
COPY src/tasks.py .
COPY src/graders.py .
COPY src/environment.py .
COPY src/main.py .

# Copy root-level files
COPY inference.py .
COPY openenv.yaml .
COPY README.md .

# Expose port 7860 (required by Hugging Face Spaces)
EXPOSE 7860

# Start the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]