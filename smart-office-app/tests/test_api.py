import unittest
from unittest.mock import patch, MagicMock
from run import app

class BasicTests(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    # אנו משתמשים ב-patch כדי "להחליף" את המונגו האמיתי בחיקוי (Mock)
    # זה מונע מהאפליקציה לנסות להתחבר לרשת ולהיכשל
    @patch('flask_pymongo.PyMongo') 
    def test_health_live(self, mock_pymongo):
        # כשהאפליקציה תבקש למחוק או לשמור, המוק יגיד "סבבה" בלי לעשות כלום
        with patch('App.blueprints.parking.mongo.db'):
            response = self.app.get('/health/live')
            self.assertEqual(response.status_code, 200)

    @patch('flask_pymongo.PyMongo')
    def test_metrics(self, mock_pymongo):
        response = self.app.get('/metrics')
        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()