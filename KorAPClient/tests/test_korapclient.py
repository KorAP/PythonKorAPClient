import unittest
from KorAPClient import KorAPConnection


class TestKorAPClient(unittest.TestCase):
    def setUp(self):
        self.kcon = KorAPConnection(verbose=True)

    def test_query(self):
        q = self.kcon.corpusQuery("Test")
        self.assertEqual(q.slots['class'], 'KorAPQuery')

    def test_frequency_query(self):
        df = self.kcon.frequencyQuery("Ameisenplage")
        self.assertGreater(df['totalResults'][0], 10)
        self.assertGreater(10000, df['totalResults'][0])

    def test_collocation_score_query(self):
        df = self.kcon.collocationScoreQuery("Ameisenplage", "heimgesucht", leftContextSize=0, rightContextSize=1)
        self.assertEquals(df['rightContextSize'][0], 1)
        self.assertGreater(df['logDice'][0], 1)
        self.assertGreater(df['pmi'][0], 10)
        self.assertLess(df['pmi'][0], 20)


    def test_corpus_stats(self):
        df = self.kcon.corpusStats(**{"as.df": True})
        self.assertGreater(df['tokens'][0], 10**10)

    def test_corpus_stats_with_vc(self):
        de_tokens = self.kcon.corpusStats(vc='pubPlaceKey="DE"', **{"as.df": True})['tokens'][0]
        ch_tokens = self.kcon.corpusStats(vc='pubPlaceKey="CH"', **{"as.df": True})['tokens'][0]
        self.assertGreater(de_tokens, ch_tokens)


if __name__ == '__main__':
    unittest.main()
