import unittest
from KorAPClient import KorAPClient

class TestKorAPClient(unittest.TestCase):
    def test_query(self):
        kcon = KorAPClient.KorAPConnection()
        q = KorAPClient.KorAPQuery(kcon, "Test")
        self.assertEqual(q.slots['class'], 'KorAPQuery')

    def test_frequency_query(self):
        kcon = KorAPClient.KorAPConnection()
        df = KorAPClient.frequencyQuery(kcon, "Ameisenplage")
        self.assertGreater(df['totalResults'][0], 10)
        self.assertGreater(10000, df['totalResults'][0])

if __name__ == '__main__':
    unittest.main()
