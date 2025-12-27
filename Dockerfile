# השתמש בגרסה המלאה - זה מונע תקיעות של קומפילציה
FROM python:3.11

WORKDIR /app

COPY requirements.txt .

# הוספנו הגבלת זמן ופירוט לוגים כדי שלא ייתקע לנצח
RUN pip install -v --timeout 100 --no-cache-dir -r requirements.txt

# העתקת התיקייה הפנימית (חובה בגלל שזה Monorepo)
COPY smart-office-app/ .

CMD ["python", "run.py"]