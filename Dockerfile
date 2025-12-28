FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

# --no-cache-dir: Reduces image size
# --prefer-binary: Avoids long compilation times for libraries
RUN pip install --prefer-binary --no-cache-dir -r requirements.txt

COPY smart-office-app/ .

CMD ["python", "run.py"]