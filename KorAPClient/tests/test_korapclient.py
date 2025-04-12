import unittest

from KorAPClient import KorAPConnection, NULL


class TestKorAPClient(unittest.TestCase):
    def setUp(self):
        self.kcon = KorAPConnection(verbose=True, accessToken=NULL)

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
    
    def test_corpus_query_token_api(self):
        q = self.kcon.corpusQuery("focus([tt/p=ADJA] {Newstickeritis})", vc="corpusSigle=/W.D17/", metadataOnly=False)
        q = q.fetchNext()
        matches = q.slots['collectedMatches']
        
        self.assertGreater(len(matches), 10)
        
        unique_matches = matches['tokens.match'].unique()
        self.assertEqual(len(unique_matches), 1)
        self.assertEqual(unique_matches[0], "Newstickeritis")
        
        left_contexts = matches['tokens.left']
        self.assertTrue(any('reine' in context for context in left_contexts))
        
        right_contexts = matches['tokens.right']
        self.assertTrue(any('Begriff' in context for context in right_contexts))
    
    def test_match_start_and_end(self):
        q = self.kcon.corpusQuery("focus([tt/p=ADJA] {Newstickeritis})", vc="corpusSigle=/W.D17/", metadataOnly=False)
        q = q.fetchNext()
        matches = q.slots['collectedMatches']
        
        self.assertGreater(matches['matchEnd'].max(), 1000)
        self.assertTrue((matches['matchEnd'] == matches['matchStart']).all())

    def test_extended_metadata_fields_ked(self):
        kcon_ked = KorAPConnection(KorAPUrl="https://korap.ids-mannheim.de/instance/ked", verbose=True)
        q = kcon_ked.corpusQuery(
            "einfache",
            fields=[
                "textSigle", "pubDate", "pubPlace", "availability", "textClass",
                "snippet", "tokens", "KED.cover1Herder", "KED.cover2Herder",
                "KED.cover3Herder", "KED.cover4Herder", "KED.cover5Herder",
                "KED.nPara", "KED.nPunct1kTks", "KED.nSent", "KED.nToks",
                "KED.nToksSentMd", "KED.nTyps", "KED.rcpnt", "KED.rcpntLabel",
                "KED.strtgy", "KED.strtgyLabel", "KED.topic", "KED.topicLabel",
                "KED.txttyp", "KED.txttypLabel"
            ]
        ).fetchAll()
        df = q.slots['collectedMatches']
        self.assertGreater(len(df), 0)
        self.assertGreater(min(df['KED.nToks'].astype(float)), 100)
        self.assertGreater(min(df['KED.nSent'].astype(float)), 8)
        self.assertGreater(min(df['KED.rcpnt'].str.len()), 5)


#    def test_authorization(self):
#        kcon = KorAPConnection(accessToken=NULL, verbose=True).auth()
#        self.assertIsNotNone(kcon.slots['accessToken'])

    def test_chained_fetch_matches(self):
        q = (
            self.kcon.corpusQuery("Test", metadataOnly=False)
            .fetchNext(maxFetch=120)
            .fetchNext()
            .fetchNext()
        )
        self.assertIn('collectedMatches', q.slots)
        self.assertEqual(len(q.slots['collectedMatches']), 220)
        self.assertIsInstance(q.slots['collectedMatches']['tokens.match'].iloc[0], str)

    def test_unchained_fetch_matches(self):
        q =  self.kcon.corpusQuery("Test", metadataOnly=False)
        q.fetchNext(maxFetch=120)
        q.fetchNext()
        q.fetchNext()
        self.assertIn('collectedMatches', q.slots)
        self.assertEqual(len(q.slots['collectedMatches']), 220)
        self.assertIsInstance(q.slots['collectedMatches']['tokens.match'].iloc[0], str)

    def test_null_strings_are_handled(self):
        q = self.kcon.corpusQuery("Der", vc="corpusSigle=WPD17", metadataOnly=False).fetchNext()
        matches = q.slots['collectedMatches']
        self.assertFalse(
            matches['tokens.left'].str.contains("rpy2.rinterface_lib.sexp.NULLType", na=False).any(),
            "The string 'rpy2.rinterface_lib.sexp.NULLType' was found in tokens.left!"
        )
        self.assertFalse(
            matches['tokens.right'].str.contains("rpy2.rinterface_lib.sexp.NULLType", na=False).any(),
            "The string 'rpy2.rinterface_lib.sexp.NULLType' was found in tokens.right!"
        )

if __name__ == '__main__':
    unittest.main()
