FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

# --prefer-binary : מונע קומפילציה (מונע תקיעות)
# --no-cache-dir : שומר על האימג' קטן
RUN pip install --prefer-binary --no-cache-dir -r requirements.txt

# העתקת התיקייה הפנימית
COPY smart-office-app/ .

CMD ["python", "run.py"]