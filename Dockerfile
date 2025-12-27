FROM python:3.11-slim

# 1. יצירת משתמש ותיקייה
RUN useradd -m appuser && mkdir /app && chown appuser:appuser /app

WORKDIR /app

# 2. העתקת ה-requirements (זה בסדר שהוא בחוץ)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- התיקון הקריטי כאן ---
# במקום COPY . . (שמעתיק את כל התיקיות)
# אנחנו מעתיקים את התוכן של תיקיית האפליקציה ישירות ל-Root של הקונטיינר
COPY smart-office-app/ .

# 4. סידור הרשאות
RUN chown -R appuser:appuser /app

USER appuser
CMD ["python", "run.py"]