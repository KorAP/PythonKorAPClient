import unittest

from KorAPClient import KorAPConnection


class TestKorAPClient(unittest.TestCase):
    def setUp(self):
        self.kcon = KorAPConnection(verbose=True)

    def test_query(self):
        q = self.kcon.corpusQuery("Test")
        self.assertEqual(q.slots['class'][0], 'KorAPQuery')

    def test_frequency_query(self):
        df = self.kcon.frequencyQuery("Ameisenplage")
        self.assertGreater(df['totalResults'].iloc[0], 10)
        self.assertGreater(10000, df['totalResults'].iloc[0])

    def test_collocation_score_query(self):
        df = self.kcon.collocationScoreQuery("Ameisenplage", "heimgesucht", leftContextSize=0, rightContextSize=1)
        self.assertEqual(df['rightContextSize'].iloc[0], 1)
        self.assertGreater(df['logDice'].iloc[0], 1)
        self.assertGreater(df['pmi'].iloc[0], 10)
        self.assertLess(df['pmi'].iloc[0], 20)

    def test_collocation_analysis(self):
        df = self.kcon.collocationAnalysis("focus([tt/p=ADJA] {Newstickeritis})", vc="corpusSigle=/W.D17/",
                                           leftContextSize=1, rightContextSize=0,
                                           searchHitsSampleLimit=1, topCollocatesLimit=1,
                                           exactFrequencies=False)
        self.assertEqual(df['rightContextSize'].iloc[0], 0)
        self.assertGreater(df['O'].iloc[0], df['E'].iloc[0])

    def test_collocation_score_query_multi_collocates(self):
        df = self.kcon.collocationScoreQuery("Ameisenplage", ["einer", "heimgesucht"], leftContextSize=1,
                                             rightContextSize=1)
        self.assertEqual(df['collocate'].iloc[1], 'heimgesucht')
        self.assertGreater(df['pmi'].iloc[1], df['pmi'].iloc[0])

    def test_corpus_stats(self):
        df = self.kcon.corpusStats()
        self.assertGreater(df['tokens'].iloc[0], 10 ** 10)

    def test_corpus_stats_with_vc(self):
        de_tokens = self.kcon.corpusStats(vc='pubPlaceKey=DE')['tokens'].iloc[0]
        ch_tokens = self.kcon.corpusStats(vc='pubPlaceKey=CH')['tokens'].iloc[0]
        self.assertGreater(de_tokens, ch_tokens)

    def test_corpus_stats_with_vc_list(self):
        tokens = self.kcon.corpusStats(vc=['pubPlaceKey=DE', 'pubPlaceKey=CH'])['tokens']
        self.assertGreater(tokens.iloc[0], tokens.iloc[1])


if __name__ == '__main__':
    unittest.main()
