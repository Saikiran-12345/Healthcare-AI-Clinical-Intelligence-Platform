import unittest
from nlp.preprocessor import ClinicalTextPreprocessor
from nlp.vectorizer import TfidfVectorizer
from nlp.symptom_matcher import SymptomMatcher
from nlp.intent_classifier import IntentClassifier
from nlp.services import NLPAnalysisService

class TestClinicalTextPreprocessor(unittest.TestCase):
    def setUp(self):
        self.prep = ClinicalTextPreprocessor()

    def test_clean_text(self):
        text = "Pt c/o severe HA & N/V."
        cleaned = self.prep.clean_text(text)
        self.assertIn("headache", cleaned)
        self.assertIn("nausea and vomiting", cleaned)

    def test_tokenize_and_stopwords(self):
        text = "I have a bad headache"
        cleaned = self.prep.clean_text(text)
        tokens = self.prep.tokenize(cleaned)
        filtered = self.prep.remove_stopwords(tokens)
        self.assertNotIn("i", filtered)
        self.assertNotIn("have", filtered)
        self.assertNotIn("a", filtered)
        self.assertIn("bad", filtered)
        self.assertIn("headache", filtered)

    def test_stemmer(self):
        self.assertEqual(self.prep.stem("running"), "run")
        self.assertEqual(self.prep.stem("tiredness"), "tired")

class TestTfidfVectorizer(unittest.TestCase):
    def setUp(self):
        self.vec = TfidfVectorizer()
        self.docs = [
            ["headache", "fever", "cough"],
            ["fever", "chills"],
            ["headache", "nausea"]
        ]

    def test_fit_transform(self):
        tfidf = self.vec.fit_transform(self.docs)
        self.assertEqual(len(tfidf), 3)
        self.assertIn("headache", self.vec.get_feature_names())
        
    def test_cosine_similarity(self):
        tfidf = self.vec.fit_transform(self.docs)
        sim = self.vec.cosine_similarity(tfidf[0], tfidf[2])
        self.assertGreater(sim, 0.0)

class TestSymptomMatcher(unittest.TestCase):
    def setUp(self):
        self.matcher = SymptomMatcher()

    def test_extract_symptoms(self):
        text = "I have been experiencing a lot of head pain and feeling very tired."
        symptoms = self.matcher.extract_symptoms(text)
        self.assertIn("headache", symptoms)
        self.assertIn("fatigue", symptoms)

    def test_fuzzy_match(self):
        self.assertTrue(self.matcher.fuzzy_match("stomch ache", "stomach ache"))
        self.assertFalse(self.matcher.fuzzy_match("headache", "stomach ache"))

class TestIntentClassifier(unittest.TestCase):
    def setUp(self):
        self.classifier = IntentClassifier()

    def test_classify_symptoms(self):
        symptoms = ["fever", "cough", "fatigue"]
        results = self.classifier.classify_symptoms(symptoms)
        self.assertTrue(len(results) > 0)
        top_diseases = [r["disease"] for r in results]
        self.assertIn("Flu/Cold", top_diseases)

    def test_urgency_level(self):
        self.assertEqual(self.classifier.get_urgency_level(["chest_pain"], []), "EMERGENCY")
        self.assertEqual(self.classifier.get_urgency_level(["rash"], []), "ROUTINE")

class TestNLPAnalysisService(unittest.TestCase):
    def setUp(self):
        self.service = NLPAnalysisService()

    def test_full_pipeline(self):
        text = "I'm having terrible chest pressure and shortness of breath."
        result = self.service.analyze_symptoms(text)
        self.assertTrue(result["success"])
        self.assertEqual(result["urgency_level"], "EMERGENCY")
        
        symptom_names = [s["id"] for s in result["symptoms"]]
        self.assertIn("chest_pain", symptom_names)
        self.assertIn("shortness_of_breath", symptom_names)

if __name__ == '__main__':
    unittest.main()
