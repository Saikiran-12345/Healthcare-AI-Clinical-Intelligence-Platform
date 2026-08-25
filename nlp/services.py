from datetime import datetime
from typing import Dict, Any, List
import uuid

from core.storage import db
from .preprocessor import ClinicalTextPreprocessor
from .symptom_matcher import SymptomMatcher
from .intent_classifier import IntentClassifier

class NLPAnalysisService:
    """Orchestration service for NLP symptom analysis."""
    
    def __init__(self):
        self.preprocessor = ClinicalTextPreprocessor()
        self.matcher = SymptomMatcher()
        self.classifier = IntentClassifier()
        
    def analyze_symptoms(self, text: str, patient_id: str = None, patient_age: int = 30, patient_gender: str = "Unknown") -> Dict[str, Any]:
        """Full NLP pipeline to analyze symptoms from text."""
        # 1. Preprocess text
        cleaned_text = self.preprocessor.clean_text(text)
        
        # 2. Extract symptoms
        extracted_symptoms = self.matcher.extract_symptoms(cleaned_text)
        
        if not extracted_symptoms:
            return {
                "success": False,
                "message": "No recognizable symptoms found in the text.",
                "original_text": text
            }
            
        # 3. Classify diseases
        disease_scores = self.classifier.classify_symptoms(extracted_symptoms)
        
        # 4. Get urgency and recommendations
        urgency = self.classifier.get_urgency_level(extracted_symptoms, disease_scores)
        specialists = self.classifier.get_recommended_specialists(disease_scores)
        
        # 5. Get risk assessment
        risk = self.classifier.get_risk_assessment(extracted_symptoms, patient_age, patient_gender)
        
        # 6. Generate summary
        summary = self.classifier.generate_clinical_summary(extracted_symptoms, disease_scores)
        
        # Format human-readable symptoms
        symptom_details = []
        for sym in extracted_symptoms:
            info = self.matcher.get_symptom_info(sym)
            symptom_details.append({
                "id": sym,
                "name": info.get("name", sym.replace("_", " ").title()),
                "severity": info.get("severity", 1),
                "system": info.get("system", "unknown")
            })
            
        result = {
            "success": True,
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "patient_id": patient_id,
            "original_text": text,
            "symptoms": symptom_details,
            "disease_scores": disease_scores,
            "urgency_level": urgency,
            "recommended_specialists": specialists,
            "risk_assessment": risk,
            "clinical_summary": summary
        }
        
        return result
        
    def save_analysis(self, patient_id: str, analysis_result: Dict[str, Any]) -> str:
        """Persist analysis to JSON storage."""
        if not analysis_result.get("success"):
            return None
            
        analysis_id = analysis_result["id"]
        
        # We will save this in predictions or a new table. Let's use predictions table
        # Since db has predictions table as per instructions
        record = {
            "id": analysis_id,
            "patient_id": patient_id,
            "type": "nlp_symptom_analysis",
            "timestamp": analysis_result["timestamp"],
            "data": analysis_result
        }
        
        db.predictions.insert(record)
        return analysis_id
        
    def get_analysis_history(self, patient_id: str) -> List[Dict[str, Any]]:
        """Retrieve past analyses for a patient."""
        # Find all predictions for this patient of type nlp_symptom_analysis
        records = db.predictions.find_all(lambda r: r.get("patient_id") == patient_id and r.get("type") == "nlp_symptom_analysis")
        
        # Sort by timestamp descending
        records.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
        return [r.get("data", {}) for r in records]
        
    def get_analysis_by_id(self, analysis_id: str) -> Dict[str, Any]:
        """Retrieve a specific analysis."""
        record = db.predictions.get_by_id(analysis_id)
        if record and record.get("type") == "nlp_symptom_analysis":
            return record.get("data", {})
        return None
        
    def get_trending_symptoms(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Aggregate most reported symptoms across all patients."""
        records = db.predictions.find_all(lambda r: r.get("type") == "nlp_symptom_analysis")
        
        symptom_counts = {}
        for r in records:
            data = r.get("data", {})
            for sym in data.get("symptoms", []):
                name = sym.get("name")
                symptom_counts[name] = symptom_counts.get(name, 0) + 1
                
        sorted_symptoms = sorted(symptom_counts.items(), key=lambda x: x[1], reverse=True)
        
        result = [{"name": name, "count": count} for name, count in sorted_symptoms[:limit]]
        return result
