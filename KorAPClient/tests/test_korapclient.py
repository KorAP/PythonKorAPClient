import os
import tempfile
import unittest

import pandas as pd

from KorAPClient import KorAPClient, KorAPConnection, NULL, hc_dispersion

LABELLED_VCS = {'Germany': 'pubPlaceKey=DE', 'Switzerland': 'pubPlaceKey=CH'}


class TestKorAPClient(unittest.TestCase):
    def setUp(self):
        self.kcon = KorAPConnection(verbose=True, accessToken=NULL)

    def test_query(self):
        q = self.kcon.corpusQuery("Test")
        self.assertEqual(q.slots['class'][0], 'KorAPQuery')

    def test_query_fetches_topic_domains_by_default(self):
        q = self.kcon.corpusQuery("Ameisenplage", vc="corpusSigle=/W.D17/").fetchNext()
        matches = q.slots['collectedMatches']
        self.assertIn('dmozDomain', matches.columns)
        self.assertIn('wikiDomain', matches.columns)

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

    def test_frequency_query_reports_query_duration(self):
        df = self.kcon.frequencyQuery("Ameisenplage")
        self.assertIn('queryDuration', df.columns)
        self.assertGreaterEqual(df['queryDuration'].iloc[0], 0)

    def test_frequency_query_with_named_vc(self):
        df = self.kcon.frequencyQuery("Ameisenplage", vc=LABELLED_VCS)
        self.assertEqual(list(df['label']), ['Germany', 'Switzerland'])
        self.assertEqual(list(df['vc']), ['pubPlaceKey=DE', 'pubPlaceKey=CH'])
        self.assertGreater(df['totalResults'].iloc[0], df['totalResults'].iloc[1])

    def test_frequency_query_cache_as(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache_file = os.path.join(tmp, "freq")
            df1 = self.kcon.frequencyQuery("Ameisenplage", cacheAs=cache_file)
            self.assertTrue(os.path.exists(cache_file + ".rds"))
            df2 = self.kcon.frequencyQuery("Ameisenplage", cacheAs=cache_file)
            self.assertEqual(df1['totalResults'].iloc[0], df2['totalResults'].iloc[0])

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

    def test_collocation_analysis_min_observed_expected_ratio(self):
        kwargs = dict(vc="corpusSigle=/W.D17/", leftContextSize=1, rightContextSize=1,
                      searchHitsSampleLimit=50, topCollocatesLimit=20, exactFrequencies=False)
        unfiltered = self.kcon.collocationAnalysis("Newstickeritis", minObservedExpectedRatio=0, **kwargs)
        filtered = self.kcon.collocationAnalysis("Newstickeritis", minObservedExpectedRatio=5000, **kwargs)
        self.assertGreater(len(unfiltered), len(filtered))
        self.assertTrue((filtered['O'] >= 5000 * filtered['E']).all())

    def test_collocation_analysis_cache_as(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache_file = os.path.join(tmp, "ca.rds")
            kwargs = dict(vc="corpusSigle=/W.D17/", leftContextSize=1, rightContextSize=0,
                          searchHitsSampleLimit=1, topCollocatesLimit=1, exactFrequencies=False,
                          cacheAs=cache_file)
            df1 = self.kcon.collocationAnalysis("focus([tt/p=ADJA] {Newstickeritis})", **kwargs)
            self.assertTrue(os.path.exists(cache_file))
            df2 = self.kcon.collocationAnalysis("focus([tt/p=ADJA] {Newstickeritis})", **kwargs)
            self.assertEqual(list(df1['collocate']), list(df2['collocate']))

    def test_collocation_score_query_with_labelled_vcs(self):
        df = self.kcon.collocationScoreQuery("Ameisenplage", "heimgesucht", vc=LABELLED_VCS,
                                             leftContextSize=0, rightContextSize=1)
        self.assertEqual(list(df['label']), ['Germany', 'Switzerland'])

    def test_collocation_score_query_with_score_functions_dict(self):
        df = self.kcon.collocationScoreQuery("Ameisenplage", "heimgesucht", leftContextSize=0, rightContextSize=1,
                                             scoreFunctions={'pmi': KorAPClient.pmi})
        self.assertIn('pmi', df.columns)
        self.assertNotIn('logDice', df.columns)

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

    def test_corpus_stats_with_named_vc(self):
        df = self.kcon.corpusStats(vc=LABELLED_VCS)
        self.assertEqual(list(df['label']), ['Germany', 'Switzerland'])

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
        self.assertTrue(any('Frachter' in context for context in right_contexts))
    
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

    def test_dispersion_query(self):
        df = self.kcon.dispersionQuery(["Ameisenplage", "Mückenplage"], by="region", vc="pubDate in 2022")
        self.assertEqual(list(df['query']), ["Ameisenplage", "Mückenplage"])
        self.assertEqual(list(df['partition']), ["region", "region"])
        self.assertGreater(df['nParts'].iloc[0], 2)
        self.assertTrue(df['DP'].between(0, 1).all())
        self.assertGreaterEqual(df['range'].iloc[1], df['range'].iloc[0])
        distribution = df['distribution'].iloc[1]
        self.assertIsInstance(distribution, pd.DataFrame)
        self.assertEqual(len(distribution), df['nParts'].iloc[1])
        self.assertIn('DE', list(distribution['part']))
        self.assertEqual(distribution['frequency'].sum(), df['usedHits'].iloc[1])
        self.assertGreater(distribution['tokens'].min(), 0)
        self.assertEqual(df['sampling'].iloc[1]['method'], 'exact_counts')

    def test_dispersion_query_with_corpus_partition(self):
        countries = self.kcon.corpusPartition("region", {"Deutschland": "DE", "Schweiz": "CH"}, vc="pubDate in 2022")
        parts = countries.toDataFrame()
        self.assertEqual(list(parts['part']), ["Deutschland", "Schweiz"])
        self.assertGreater(parts['tokens'].iloc[0], parts['tokens'].iloc[1])
        df = self.kcon.dispersionQuery("Mückenplage", partitions=countries,
                                       scoreFunctions={'DP': KorAPClient.dispersionDP})
        self.assertEqual(df['nParts'].iloc[0], 2)
        self.assertIn('DP', df.columns)
        self.assertNotIn('JuillandD', df.columns)
        self.assertEqual(list(df['distribution'].iloc[0]['part']), ["Deutschland", "Schweiz"])

    def test_corpus_partition_by_year(self):
        years = self.kcon.corpusPartition("year", [2021, 2022], vc="pubDate in 2021 | pubDate in 2022")
        self.assertEqual(list(years.toDataFrame()['part']), ["2021", "2022"])

    def test_dispersion_analysis(self):
        q = self.kcon.corpusQuery("Mückenplage", vc="pubDate in 2022")
        df = q.dispersionAnalysis(by="region")
        self.assertEqual(df['query'].iloc[0], "Mückenplage")
        self.assertEqual(df['totalResults'].iloc[0], q.slots['totalResults'][0])
        self.assertFalse(df['estimated'].iloc[0])
        for measure in ['DP', 'DPnorm', 'JuillandD', 'CarrollD2', 'RosengrenS', 'range']:
            self.assertIn(measure, df.columns)

    def test_dispersion_analysis_of_sampled_pages(self):
        q = self.kcon.corpusQuery("Ameise", vc="pubDate in 2022").fetchSamplePages(maxHits=100, seed=3)
        matches = q.slots['collectedMatches']
        self.assertEqual(len(matches), 100)
        self.assertIsInstance(matches['dmozDomain'].dropna().iloc[0], str)
        df = q.dispersionAnalysis(by="region")
        self.assertTrue(df['estimated'].iloc[0])
        self.assertEqual(df['sampledHits'].iloc[0], 100)
        self.assertEqual(df['sampling'].iloc[0]['method'], 'random_pages')
        self.assertEqual(df['sampling'].iloc[0]['seed'], 3)


    def test_maintenance_info(self):
        info = self.kcon.maintenanceInfo(refresh=True)
        self.assertIn(info['state'], ["ok", "stale", "unknown", "unsupported"])
        self.assertIsInstance(info['events'], pd.DataFrame)
        for column in ['start', 'end', 'start_epoch', 'end_epoch', 'all_day', 'ongoing']:
            self.assertIn(column, info['events'].columns)

    def test_hc_dispersion(self):
        df = self.kcon.dispersionQuery(["Ameisenplage", "Mückenplage"], by="region", vc="pubDate in 2022")
        df["query"] = df["query"].map({"Ameisenplage": "Ameisen", "Mückenplage": "Mücken"})
        chart = hc_dispersion(df, partition="region", top=3)
        with tempfile.TemporaryDirectory() as directory:
            path = chart.save(os.path.join(directory, "dispersion.html"))
            with open(path, encoding="utf-8") as file:
                html = file.read()
        self.assertIn("Mücken", html)
        self.assertIn("Remaining 4 parts", html)
        self.assertIn("<iframe", chart._repr_html_())
        with self.assertRaises(ValueError):
            hc_dispersion(df[["query", "partition"]])


if __name__ == '__main__':
    unittest.main()
