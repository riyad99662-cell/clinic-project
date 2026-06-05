import json
import re
import requests

from django.conf import settings

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def analyze_symptoms(symptoms):

    prompt = f"""
You are a medical AI assistant.

Analyze these symptoms:

{symptoms}

Return ONLY valid JSON.

Format:

{{
    "diagnosis": "",
    "recommendation": "",
    "severity": ""
}}
"""

    headers = {
        "HTTP_AUTHORIZATION": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "Referer": "https://clinic-api.onrender.com",
        "X-Title": "Clinic AI",
    }

    payload = {
        "model": "meta-llama/llama-3.1-8b-instruct",
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "temperature": 0.3,
    }

    response = requests.post(
        OPENROUTER_URL,
        headers=headers,
        json=payload,
        timeout=30,
    )

    print(response.status_code)
    print(response.text)

    data = response.json()

    content = data["choices"][0]["message"]["content"]

    match = re.search(r"\{.*\}", content, re.DOTALL)

    if not match:
        return None

    clean_json = match.group()

    return json.loads(clean_json)


###


def generate_clinical_insight(data):

    prompt = f"""
    You are an advanced clinical AI assistant.

    Analyze the patient case carefully.

    Patient Information:
    {json.dumps(data, indent=2)}

    Return ONLY valid JSON.

    Risk score guidelines:

    0-20:
    Low risk
    
    21-50:
    Moderate risk
    
    51-80:
    High risk
    
    81-100:
    Critical risk
    
    Increase score if:
    - abnormal vitals
    - severe symptoms
    - chronic disease
    - dangerous history
    - respiratory issues
    - cardiac symptoms
    
    JSON format:
    {{
        "risk_score": 0,
        "summary": "",
        "differential_diagnosis": [
            {{
                "name": "",
                "probability": ""
            }}
        ],
        "recommendations": [
            ""
        ]
    }}
    """

    headers = {
        "HTTP_AUTHORIZATION": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "Referer": "https://clinic-api.onrender.com",
        "X-Title": "Clinic AI",
    }

    payload = {
        "model": "meta-llama/llama-3.1-8b-instruct",
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "temperature": 0.3,
    }

    response = requests.post(
        OPENROUTER_URL,
        headers=headers,
        json=payload,
        timeout=60,
    )

    response.raise_for_status()

    result = response.json()

    content = result["choices"][0]["message"]["content"]

    match = re.search(r"\{.*\}", content, re.DOTALL)

    if not match:
        return None

    clean_json = match.group()

    return json.loads(clean_json)
