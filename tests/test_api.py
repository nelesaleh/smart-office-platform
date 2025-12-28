import unittest
import sys
import os

# הוספת התיקייה smart-office-app ל-Path כדי שנצליח לייבא את run.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../smart-office-app')))

from run import app

class BasicTests(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_health_live(self):
        # בודק שהנתיב /health/live מחזיר 200
        response = self.app.get('/health/live')
        self.assertEqual(response.status_code, 200)

    def test_metrics(self):
        # בודק שהנתיב /metrics מחזיר 200
        response = self.app.get('/metrics')
        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()