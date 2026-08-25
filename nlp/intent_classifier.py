from typing import List, Dict, Tuple, Any
from .symptom_matcher import SymptomMatcher

# Matrix mapping diseases to their common symptoms with weights (0.0 to 1.0)
DISEASE_SYMPTOM_MATRIX = {
    "Diabetes": {
        "frequent_urination": 0.9,
        "excessive_thirst": 0.9,
        "fatigue": 0.7,
        "weight_loss": 0.6,
        "blurry_vision": 0.5,
        "nausea": 0.2
    },
    "Heart Disease": {
        "chest_pain": 0.9,
        "shortness_of_breath": 0.8,
        "fatigue": 0.6,
        "dizziness": 0.5,
        "swelling": 0.7,
        "nausea": 0.3
    },
    "Hypertension": {
        "headache": 0.7,
        "dizziness": 0.6,
        "blurry_vision": 0.4,
        "shortness_of_breath": 0.5,
        "chest_pain": 0.3
    },
    "Kidney Disease": {
        "frequent_urination": 0.7,
        "swelling": 0.8,
        "fatigue": 0.6,
        "nausea": 0.5,
        "abdominal_pain": 0.4
    },
    "Respiratory Infections": {
        "cough": 0.9,
        "fever": 0.8,
        "shortness_of_breath": 0.7,
        "fatigue": 0.6,
        "chest_pain": 0.4
    },
    "Flu/Cold": {
        "fever": 0.8,
        "cough": 0.7,
        "fatigue": 0.7,
        "headache": 0.6,
        "joint_pain": 0.5
    },
    "Gastric Issues": {
        "abdominal_pain": 0.9,
        "nausea": 0.8,
        "vomiting": 0.7,
        "diarrhea": 0.7,
        "fatigue": 0.3
    },
    "Anemia": {
        "fatigue": 0.9,
        "dizziness": 0.7,
        "shortness_of_breath": 0.6,
        "chest_pain": 0.2
    },
    "Thyroid": {
        "fatigue": 0.8,
        "weight_loss": 0.7,
        "frequent_urination": 0.3
    },
    "Arthritis": {
        "joint_pain": 0.9,
        "fatigue": 0.4,
        "swelling": 0.6
    }
}

class IntentClassifier:
    """Symptom-to-disease correlation analyzer."""
    
    def __init__(self):
        self.matcher = SymptomMatcher()
        self.disease_matrix = DISEASE_SYMPTOM_MATRIX
        
    def classify_symptoms(self, symptoms_list: List[str]) -> List[Dict[str, Any]]:
        """Given extracted symptoms, compute disease probability scores."""
        if not symptoms_list:
            return []
            
        disease_scores = {}
        
        for disease, symptom_weights in self.disease_matrix.items():
            score = 0.0
            max_possible_score = sum(symptom_weights.values())
            
            if max_possible_score == 0:
                continue
                
            matched_symptoms = []
            
            for sym in symptoms_list:
                if sym in symptom_weights:
                    score += symptom_weights[sym]
                    matched_symptoms.append(sym)
                    
            # Normalize score
            if score > 0:
                probability = (score / max_possible_score) * 100
                # Give a boost for having multiple symptoms of the disease
                match_ratio = len(matched_symptoms) / len(symptom_weights)
                probability = min(probability * (1 + match_ratio * 0.5), 95.0) # Cap at 95%
                
                if probability > 5.0: # Only return diseases with > 5% probability
                    disease_scores[disease] = {
                        "disease": disease,
                        "probability": round(probability, 1),
                        "matched_symptoms": matched_symptoms
                    }
                    
        # Sort by probability descending
        sorted_results = sorted(disease_scores.values(), key=lambda x: x["probability"], reverse=True)
        return sorted_results[:5] # Return top 5
        
    def get_urgency_level(self, symptoms: List[str], disease_scores: List[Dict[str, Any]]) -> str:
        """Return urgency: ROUTINE, MODERATE, URGENT, EMERGENCY."""
        severity = self.matcher.calculate_symptom_severity(symptoms)
        
        # Check for emergency symptoms regardless of diseases
        emergency_symptoms = ["chest_pain", "shortness_of_breath"]
        if any(sym in emergency_symptoms for sym in symptoms):
            if severity >= 4:
                return "EMERGENCY"
                
        if severity >= 7:
            return "EMERGENCY"
        elif severity >= 5:
            return "URGENT"
        elif severity >= 3:
            return "MODERATE"
        else:
            return "ROUTINE"
            
    def get_recommended_specialists(self, disease_scores: List[Dict[str, Any]]) -> List[str]:
        """Map top diseases to specialist types."""
        specialist_map = {
            "Diabetes": "Endocrinologist",
            "Heart Disease": "Cardiologist",
            "Hypertension": "Cardiologist or General Physician",
            "Kidney Disease": "Nephrologist",
            "Respiratory Infections": "Pulmonologist or ENT",
            "Flu/Cold": "General Physician",
            "Gastric Issues": "Gastroenterologist",
            "Anemia": "Hematologist or General Physician",
            "Thyroid": "Endocrinologist",
            "Arthritis": "Rheumatologist"
        }
        
        specialists = set()
        for idx, ds in enumerate(disease_scores):
            # Only consider top 2 diseases or diseases with > 40% probability
            if idx < 2 or ds["probability"] > 40:
                disease = ds["disease"]
                if disease in specialist_map:
                    specialists.add(specialist_map[disease])
                    
        if not specialists:
            specialists.add("General Physician")
            
        return list(specialists)

    def get_risk_assessment(self, symptoms: List[str], patient_age: int, patient_gender: str) -> Dict[str, Any]:
        """Detailed risk assessment."""
        base_severity = self.matcher.calculate_symptom_severity(symptoms)
        
        # Age modifier
        age_risk = 0
        if patient_age > 65:
            age_risk = 2
        elif patient_age > 50:
            age_risk = 1
            
        adjusted_severity = min(base_severity + age_risk, 10)
        
        return {
            "base_severity": base_severity,
            "adjusted_severity": adjusted_severity,
            "age_factor_applied": age_risk > 0,
            "risk_level": "High" if adjusted_severity >= 7 else "Medium" if adjusted_severity >= 4 else "Low"
        }

    def generate_clinical_summary(self, symptoms: List[str], disease_scores: List[Dict[str, Any]]) -> str:
        """Natural language summary."""
        if not symptoms:
            return "No recognized clinical symptoms were identified."
            
        symptom_names = [self.matcher.get_symptom_info(s).get("name", s.replace("_", " ")) for s in symptoms]
        sym_text = ", ".join(symptom_names[:-1]) + (" and " if len(symptom_names) > 1 else "") + symptom_names[-1]
        
        summary = f"Patient presents with {sym_text}."
        
        if disease_scores:
            top_disease = disease_scores[0]["disease"]
            prob = disease_scores[0]["probability"]
            summary += f" Symptom profile most closely aligns with {top_disease} ({prob}% match)."
            
            if len(disease_scores) > 1:
                summary += f" Other differential considerations include {disease_scores[1]['disease']}."
        else:
            summary += " Symptom profile does not strongly match common predefined conditions."
            
        return summary
