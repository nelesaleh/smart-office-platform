import unittest
from unittest.mock import patch, MagicMock
from run import app

class BasicTests(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    # הטלאי (Patch) חייב להיות כאן כדי למנוע חיבור ל-DB האמיתי
    @patch('App.blueprints.parking.mongo')
    def test_health_live(self, mock_parking_mongo):
        # מלמדים את ה-Mock להחזיר 0 כשהאפליקציה שואלת "כמה מסמכים יש?"
        # זה פותר את שגיאת ה-TypeError שהייתה קודם
        mock_parking_mongo.db.parking_spots.count_documents.return_value = 0
        
        # מלמדים את ה-Mock לא לקרוס כשהאפליקציה מנסה למחוק נתונים
        mock_parking_mongo.db.parking_spots.delete_many.return_value.deleted_count = 0

        # הרצת הבדיקה בפועל
        response = self.app.get('/health/live')
        self.assertEqual(response.status_code, 200)

    @patch('App.blueprints.parking.mongo')
    def test_metrics(self, mock_parking_mongo):
        # גם כאן צריך להגדיר את זה, כי הקוד רץ בכל בקשה
        mock_parking_mongo.db.parking_spots.count_documents.return_value = 0
        
        response = self.app.get('/metrics')
        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()