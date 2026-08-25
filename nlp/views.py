from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.urls import reverse
import json

from accounts.decorators import login_required_json, patient_required
from core.storage import db
from .services import NLPAnalysisService

nlp_service = NLPAnalysisService()

def symptom_checker_view(request):
    """GET shows form, POST processes symptoms and shows results."""
    context = {}
    
    if request.method == "POST":
        text = request.POST.get("symptoms", "")
        if not text:
            context["error"] = "Please describe your symptoms."
            return render(request, "nlp/symptom_checker.html", context)
            
        # Get patient details if logged in
        patient_id = None
        patient_age = 30
        patient_gender = "Unknown"
        
        user_id = request.session.get("user_id")
        if user_id:
            user = db.users.get_by_id(user_id)
            if user and user.get("role") == "patient":
                patient_id = user_id
                patient_record = db.patients.find_one(lambda p: p.get("user_id") == user_id)
                if patient_record:
                    patient_age = patient_record.get("age", 30)
                    patient_gender = patient_record.get("gender", "Unknown")
                    
        # Analyze
        result = nlp_service.analyze_symptoms(text, patient_id, patient_age, patient_gender)
        
        if result.get("success"):
            # Save if logged in
            if patient_id:
                nlp_service.save_analysis(patient_id, result)
            context["result"] = result
        else:
            context["error"] = result.get("message", "Could not analyze symptoms.")
            context["original_text"] = text
            
    return render(request, "nlp/symptom_checker.html", context)

def symptom_history_view(request):
    """View past NLP analyses for current patient."""
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("accounts:login")
        
    user = db.users.get_by_id(user_id)
    if not user or user.get("role") != "patient":
        return redirect("dashboard")
        
    history = nlp_service.get_analysis_history(user_id)
    context = {
        "history": history
    }
    return render(request, "nlp/symptom_history.html", context)

def symptom_detail_view(request, analysis_id):
    """Detailed view of one analysis."""
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("accounts:login")
        
    analysis = nlp_service.get_analysis_by_id(analysis_id)
    
    if not analysis:
        return render(request, "nlp/symptom_detail.html", {"error": "Analysis not found."})
        
    # Check permissions (user must own this analysis or be a doctor)
    user = db.users.get_by_id(user_id)
    is_doctor = user and user.get("role") == "doctor"
    
    if not is_doctor and analysis.get("patient_id") != user_id:
        return render(request, "nlp/symptom_detail.html", {"error": "Unauthorized access."})
        
    context = {
        "analysis": analysis
    }
    return render(request, "nlp/symptom_detail.html", context)

def api_analyze_symptoms(request):
    """JSON API endpoint for symptom analysis."""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
        
    try:
        data = json.loads(request.body)
        text = data.get("text", "")
        
        if not text:
            return JsonResponse({"error": "Text is required"}, status=400)
            
        result = nlp_service.analyze_symptoms(text)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
