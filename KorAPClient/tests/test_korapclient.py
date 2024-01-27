import unittest

from KorAPClient import KorAPConnection


class TestKorAPClient(unittest.TestCase):
    def setUp(self):
        self.kcon = KorAPConnection(verbose=True)

    def test_query(self):
        q = self.kcon.corpusQuery("Test")
        self.assertEqual(q.slots['class'][0], 'KorAPQuery')

    def test_query_with_snippets(self):
        q = self.kcon.corpusQuery("Ameisenplage", metadataOnly=False).fetchNext()
        self.assertIn('collectedMatches', q.slots)
        self.assertIsInstance(q.slots['collectedMatches']['tokens.match'].iloc[0], str)

    def test_query_with_snippets_is_tokenized_with_fetch_next(self):
        q = self.kcon.corpusQuery("Ameisenplage", metadataOnly=False).fetchNext()
        self.assertIsInstance(q.slots['collectedMatches']['tokens.left'].iloc[0], str)
        self.assertIsInstance(q.slots['collectedMatches']['tokens.match'].iloc[0], str)
        self.assertIsInstance(q.slots['collectedMatches']['tokens.right'].iloc[0], str)
        left_contexts = "".join(q.slots['collectedMatches']['tokens.left'])
        self.assertIn('\t', left_contexts)

    def test_query_with_snippets_is_tokenized_with_fetch_all(self):
        q = self.kcon.corpusQuery("Ameisenplage", metadataOnly=False).fetchAll()
        self.assertIsInstance(q.slots['collectedMatches']['tokens.left'].iloc[0], str)
        self.assertIsInstance(q.slots['collectedMatches']['tokens.match'].iloc[0], str)
        self.assertIsInstance(q.slots['collectedMatches']['tokens.right'].iloc[0], str)
        left_contexts = "".join(q.slots['collectedMatches']['tokens.left'])
        self.assertIn('\t', left_contexts)

    def test_query_with_snippets_is_tokenized_with_fetch_rest(self):
        q = self.kcon.corpusQuery("Ameisenplage", metadataOnly=False).fetchRest()
        self.assertIsInstance(q.slots['collectedMatches']['tokens.left'].iloc[0], str)
        self.assertIsInstance(q.slots['collectedMatches']['tokens.match'].iloc[0], str)
        self.assertIsInstance(q.slots['collectedMatches']['tokens.right'].iloc[0], str)
        self.assertIsInstance(q.slots['collectedMatches']['textSigle'].iloc[1], str)
        left_contexts = "".join(q.slots['collectedMatches']['tokens.left'])
        self.assertIn('\t', left_contexts)

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

    def test_textMetadata(self):
        df = self.kcon.textMetadata(["WUD17/A97/08542", "WUD17/B96/57558", "WUD17/A97/08541"])
        self.assertEqual(len(df), 3)
        self.assertIn('textSigle', df.columns)
        self.assertIn('title', df.columns)
        self.assertIn('pubDate', df.columns)
        self.assertIn('creationDate', df.columns)
        self.assertIn('pubPlace', df.columns)
        self.assertIn('author', df.columns)


if __name__ == '__main__':
    unittest.main()
