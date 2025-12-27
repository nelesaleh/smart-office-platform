FROM python:3.11-slim

# הגדרת תיקיית עבודה
WORKDIR /app

# העתקת דרישות והתקנה
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# העתקת קוד האפליקציה (מהתיקייה הפנימית לתיקייה הנוכחית)
COPY smart-office-app/ .

# הרצה (ללא USER appuser)
CMD ["python", "run.py"]