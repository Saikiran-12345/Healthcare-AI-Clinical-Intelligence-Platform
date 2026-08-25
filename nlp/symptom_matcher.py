import re
from typing import List, Dict, Tuple, Any

# A comprehensive dictionary mapping symptoms to their details
SYMPTOM_DATABASE = {
    "fever": {
        "name": "Fever",
        "synonyms": ["high temperature", "feverish", "chills", "hot flashes", "pyrexia", "hyperthermia"],
        "system": "systemic",
        "severity": 2,
        "diseases": ["Flu/Cold", "Respiratory Infections", "Malaria", "COVID-19", "Typhoid"]
    },
    "headache": {
        "name": "Headache",
        "synonyms": ["head pain", "cephalalgia", "head ache", "migraine", "pounding head", "head pressure"],
        "system": "neurological",
        "severity": 2,
        "diseases": ["Flu/Cold", "Hypertension", "Migraine", "Stress"]
    },
    "cough": {
        "name": "Cough",
        "synonyms": ["coughing", "hacking", "chesty", "dry cough", "productive cough"],
        "system": "respiratory",
        "severity": 1,
        "diseases": ["Flu/Cold", "Respiratory Infections", "Asthma", "Tuberculosis"]
    },
    "fatigue": {
        "name": "Fatigue",
        "synonyms": ["tiredness", "exhaustion", "lethargy", "weakness", "lack of energy", "run down"],
        "system": "systemic",
        "severity": 2,
        "diseases": ["Anemia", "Diabetes", "Heart Disease", "Thyroid", "Depression"]
    },
    "chest_pain": {
        "name": "Chest Pain",
        "synonyms": ["chest pressure", "angina", "tight chest", "heart pain", "chest tightness"],
        "system": "cardiovascular",
        "severity": 5,
        "diseases": ["Heart Disease", "Heart Attack", "Acid Reflux", "Respiratory Infections"]
    },
    "shortness_of_breath": {
        "name": "Shortness of Breath",
        "synonyms": ["breathlessness", "dyspnea", "trouble breathing", "can't catch breath", "wheezing"],
        "system": "respiratory",
        "severity": 4,
        "diseases": ["Heart Disease", "Asthma", "COPD", "Anxiety", "Respiratory Infections"]
    },
    "nausea": {
        "name": "Nausea",
        "synonyms": ["feeling sick", "queasy", "stomach sickness", "want to vomit", "sick to stomach"],
        "system": "gastrointestinal",
        "severity": 2,
        "diseases": ["Gastric Issues", "Food Poisoning", "Migraine", "Pregnancy"]
    },
    "vomiting": {
        "name": "Vomiting",
        "synonyms": ["throwing up", "puking", "emesis", "barfing", "heaving"],
        "system": "gastrointestinal",
        "severity": 3,
        "diseases": ["Gastric Issues", "Food Poisoning", "Gastroenteritis"]
    },
    "diarrhea": {
        "name": "Diarrhea",
        "synonyms": ["loose stools", "watery stool", "the runs", "bowel issues"],
        "system": "gastrointestinal",
        "severity": 2,
        "diseases": ["Gastric Issues", "Food Poisoning", "IBS"]
    },
    "abdominal_pain": {
        "name": "Abdominal Pain",
        "synonyms": ["stomach ache", "belly pain", "tummy ache", "stomach cramps", "gut pain"],
        "system": "gastrointestinal",
        "severity": 3,
        "diseases": ["Gastric Issues", "Kidney Disease", "Appendicitis", "Ulcer"]
    },
    "dizziness": {
        "name": "Dizziness",
        "synonyms": ["lightheaded", "vertigo", "faint", "woozy", "spinning", "passing out"],
        "system": "neurological",
        "severity": 3,
        "diseases": ["Hypertension", "Anemia", "Heart Disease", "Dehydration"]
    },
    "joint_pain": {
        "name": "Joint Pain",
        "synonyms": ["arthralgia", "aching joints", "sore joints", "knee pain", "stiff joints"],
        "system": "musculoskeletal",
        "severity": 2,
        "diseases": ["Arthritis", "Lupus", "Gout", "Flu/Cold"]
    },
    "frequent_urination": {
        "name": "Frequent Urination",
        "synonyms": ["peeing a lot", "polyuria", "always needing to pee", "frequent peeing"],
        "system": "urinary",
        "severity": 2,
        "diseases": ["Diabetes", "Kidney Disease", "UTI", "Prostate Issues"]
    },
    "excessive_thirst": {
        "name": "Excessive Thirst",
        "synonyms": ["polydipsia", "always thirsty", "dry mouth", "drinking a lot"],
        "system": "systemic",
        "severity": 2,
        "diseases": ["Diabetes", "Dehydration", "Kidney Disease"]
    },
    "weight_loss": {
        "name": "Unexplained Weight Loss",
        "synonyms": ["losing weight", "dropping pounds", "thinning", "wasting"],
        "system": "systemic",
        "severity": 3,
        "diseases": ["Diabetes", "Thyroid", "Cancer", "Depression"]
    },
    "swelling": {
        "name": "Swelling (Edema)",
        "synonyms": ["edema", "puffy", "swollen ankles", "swollen legs", "bloating", "fluid retention"],
        "system": "cardiovascular",
        "severity": 3,
        "diseases": ["Heart Disease", "Kidney Disease", "Liver Disease"]
    },
    "blurry_vision": {
        "name": "Blurry Vision",
        "synonyms": ["can't see clearly", "fuzzy vision", "vision problems", "impaired sight"],
        "system": "neurological",
        "severity": 3,
        "diseases": ["Diabetes", "Hypertension", "Cataracts", "Stroke"]
    },
    "rash": {
        "name": "Skin Rash",
        "synonyms": ["redness", "hives", "itchy skin", "welts", "skin breakout"],
        "system": "dermatological",
        "severity": 1,
        "diseases": ["Allergies", "Measles", "Eczema", "Lupus"]
    }
}

class SymptomMatcher:
    """Clinical symptom matching engine."""
    
    def __init__(self):
        self.symptom_db = SYMPTOM_DATABASE
        
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate the Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
            
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
            
        return previous_row[-1]
        
    def fuzzy_match(self, term: str, target: str, threshold: float = 0.8) -> bool:
        """Simple character-level similarity matching using Levenshtein distance."""
        term = term.lower().strip()
        target = target.lower().strip()
        
        if not term or not target:
            return False
            
        if term == target or term in target or target in term:
            return True
            
        distance = self._levenshtein_distance(term, target)
        max_len = max(len(term), len(target))
        similarity = 1 - (distance / max_len)
        
        return similarity >= threshold

    def extract_symptoms(self, text: str) -> List[str]:
        """Extract recognized symptoms from free text."""
        text = text.lower()
        extracted = set()
        
        # Simple n-gram approach for multi-word symptoms
        words = re.findall(r'\b\w+\b', text)
        
        # Check unigrams, bigrams, and trigrams
        for n in range(1, 4):
            if len(words) < n:
                continue
            for i in range(len(words) - n + 1):
                phrase = " ".join(words[i:i+n])
                
                # Check against database
                for sym_key, sym_data in self.symptom_db.items():
                    # Check canonical name
                    if self.fuzzy_match(phrase, sym_data["name"].lower(), 0.85):
                        extracted.add(sym_key)
                        
                    # Check synonyms
                    for synonym in sym_data["synonyms"]:
                        if self.fuzzy_match(phrase, synonym.lower(), 0.85):
                            extracted.add(sym_key)
                            break
                            
        return list(extracted)
        
    def get_symptom_info(self, symptom_key: str) -> Dict[str, Any]:
        """Look up symptom details."""
        return self.symptom_db.get(symptom_key, {})
        
    def find_related_symptoms(self, symptom_key: str) -> List[str]:
        """Find symptoms in same body system."""
        info = self.get_symptom_info(symptom_key)
        if not info:
            return []
            
        target_system = info.get("system")
        related = []
        
        for key, data in self.symptom_db.items():
            if key != symptom_key and data.get("system") == target_system:
                related.append(key)
                
        return related
        
    def calculate_symptom_severity(self, symptoms: List[str]) -> int:
        """Aggregate severity score from multiple symptoms (1-10 scale)."""
        if not symptoms:
            return 0
            
        total_severity = 0
        max_individual_severity = 0
        
        for sym in symptoms:
            info = self.get_symptom_info(sym)
            if info:
                sev = info.get("severity", 1)
                total_severity += sev
                if sev > max_individual_severity:
                    max_individual_severity = sev
                    
        # Base score is the maximum individual severity
        # We add a small bonus for having multiple symptoms, capped at 10
        bonus = min((len(symptoms) - 1) * 0.5, 3) # Max +3 for multiple symptoms
        
        final_score = int(round(max_individual_severity + bonus))
        return min(max(final_score, 1), 10)
