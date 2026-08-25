import re
import string
from typing import List, Set, Dict

class ClinicalTextPreprocessor:
    """
    A comprehensive clinical text preprocessing engine.
    """
    
    def __init__(self):
        # 150+ common english stopwords
        self.stopwords: Set[str] = {
            "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", 
            "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", 
            "herself", "it", "its", "itself", "they", "them", "their", "theirs", "themselves", 
            "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are", 
            "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", 
            "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until", 
            "while", "of", "at", "by", "for", "with", "about", "against", "between", "into", 
            "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", 
            "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", 
            "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", 
            "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", 
            "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now",
            "feel", "feeling", "feels", "felt", "got", "get", "getting", "gets", "patient",
            "doctor", "dr", "mr", "mrs", "ms", "hospital", "clinic", "day", "days", "week", 
            "weeks", "month", "months", "year", "years", "today", "yesterday", "tomorrow",
            "morning", "afternoon", "evening", "night", "since", "ago", "started", "began"
        }
        
        self.medical_abbreviations: Dict[str, str] = {
            "bp": "blood pressure",
            "hr": "heart rate",
            "sob": "shortness of breath",
            "c/o": "complains of",
            "hx": "history",
            "dx": "diagnosis",
            "rx": "prescription",
            "tx": "treatment",
            "sx": "symptoms",
            "rt": "right",
            "lt": "left",
            "n/v": "nausea and vomiting",
            "ha": "headache",
            "gi": "gastrointestinal",
            "cv": "cardiovascular",
            "cns": "central nervous system",
            "wfl": "within functional limits",
            "wnl": "within normal limits",
            "y/o": "years old",
            "yo": "years old",
            "prn": "as needed",
            "stat": "immediately",
            "dob": "date of birth",
            "htn": "hypertension",
            "dm": "diabetes mellitus",
            "cad": "coronary artery disease",
            "chf": "congestive heart failure",
            "copd": "chronic obstructive pulmonary disease",
            "cva": "cerebrovascular accident",
            "tia": "transient ischemic attack",
            "mi": "myocardial infarction",
            "uti": "urinary tract infection",
            "uri": "upper respiratory infection"
        }

    def normalize_medical_terms(self, text: str) -> str:
        """Map common medical abbreviations to full terms."""
        words = text.split()
        normalized_words = []
        for word in words:
            clean_word = word.lower().strip(string.punctuation)
            if clean_word in self.medical_abbreviations:
                # Replace but keep original punctuation logic simplified
                normalized_words.append(self.medical_abbreviations[clean_word])
            else:
                normalized_words.append(word)
        return " ".join(normalized_words)

    def clean_text(self, text: str) -> str:
        """Remove special chars, normalize whitespace, lowercase."""
        if not text:
            return ""
        
        # Lowercase
        text = text.lower()
        
        # Normalize medical terms before removing punctuation
        text = self.normalize_medical_terms(text)
        
        # Remove punctuation except spaces
        text = re.sub(f"[{re.escape(string.punctuation)}]", " ", text)
        
        # Remove numbers (optional, but often good for symptom matching)
        text = re.sub(r"\d+", " ", text)
        
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()
        
        return text

    def tokenize(self, text: str) -> List[str]:
        """Split text into word tokens."""
        return text.split()

    def remove_stopwords(self, tokens: List[str]) -> List[str]:
        """Filter common English stopwords."""
        return [token for token in tokens if token not in self.stopwords]

    def stem(self, word: str) -> str:
        """Simple Porter-style stemmer (basic rules)."""
        if len(word) <= 3:
            return word
            
        suffixes = [
            ("ing", ""), ("tion", ""), ("ed", ""), ("ly", ""), ("ness", ""),
            ("ment", ""), ("able", ""), ("ible", ""), ("ous", ""), ("ive", ""),
            ("ful", ""), ("less", ""), ("est", ""), ("er", ""), ("al", ""),
            ("ity", ""), ("ize", ""), ("ise", ""), ("s", "")
        ]
        
        for suffix, replacement in suffixes:
            if word.endswith(suffix):
                # Basic check to ensure the stem isn't too short
                stemmed = word[:-len(suffix)] + replacement
                if suffix == "ing" and len(stemmed) > 3 and stemmed[-1] == stemmed[-2]:
                    stemmed = stemmed[:-1]
                if len(stemmed) >= 3:
                    return stemmed
        return word

    def preprocess(self, text: str, apply_stemming: bool = False) -> List[str]:
        """Full pipeline: clean -> tokenize -> remove stopwords -> (optional) stem."""
        cleaned = self.clean_text(text)
        tokens = self.tokenize(cleaned)
        filtered_tokens = self.remove_stopwords(tokens)
        
        if apply_stemming:
            return [self.stem(token) for token in filtered_tokens]
        return filtered_tokens

    def extract_ngrams(self, tokens: List[str], n: int) -> List[str]:
        """Generate n-grams from token list."""
        if len(tokens) < n:
            return []
        
        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngrams.append(" ".join(tokens[i:i+n]))
        return ngrams
