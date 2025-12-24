# Use a lightweight Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# 1. Copy requirements file and install dependencies
# Since requirements.txt is in the root directory, we copy it directly
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Copy the application code
# We copy the contents of the 'smart-office-app' subfolder into the container's working directory
COPY smart-office-app/ .

# 3. Create a non-root user for security (Best Practice)
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# 4. Expose port 5000 for the Flask application
EXPOSE 5000

# 5. Command to run the application
CMD ["python", "run.py"]