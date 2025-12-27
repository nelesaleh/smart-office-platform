FROM python:3.11-slim

# 1. צור את המשתמש והתיקייה בהתחלה (זה יישמר ב-Cache ולא ירוץ כל פעם מחדש)
RUN useradd -m appuser && mkdir /app && chown appuser:appuser /app

WORKDIR /app

# 2. העתק והתקן דרישות (לפני הקוד עצמו)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. העתק את שאר הקוד
COPY . .

# 4. שנה הרשאות רק לקבצים החדשים שהועתקו (מהיר יותר)
RUN chown -R appuser:appuser /app

USER appuser
CMD ["python", "run.py"]