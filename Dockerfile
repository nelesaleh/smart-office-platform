# Use a lightweight Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# 1. Create a non-root user FIRST
RUN useradd -m appuser

# 2. Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy the application code AND change ownership in ONE step
# This prevents the "hang" caused by running 'chown -R' later
COPY --chown=appuser:appuser smart-office-app/ .

# 4. Switch to non-root user
USER appuser

# 5. Expose port 5000
EXPOSE 5000

# 6. Command to run the application using Gunicorn (Production ready!)
# Assumes your flask object is named 'app' inside 'run.py'
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]