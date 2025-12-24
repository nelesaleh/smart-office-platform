# Use a lightweight Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# 1. Copy requirements file and install dependencies
# (بما أنه في الجذر، ننسخه مباشرة)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Copy the application code specifically
# (ننسخ محتويات المجلد الفرعي smart-office-app إلى داخل الحاوية)
COPY smart-office-app/ .

# 3. Create a non-root user for security
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# 4. Expose port 5000
EXPOSE 5000

# 5. Command to run the application
CMD ["python", "run.py"]