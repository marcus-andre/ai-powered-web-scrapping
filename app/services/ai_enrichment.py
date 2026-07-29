import os
import google.generativeai as genai
from google.genai import types
from app.models import DataAnalysisResult


def analyze_content_with_gemini(raw_text: str) -> DataAnalysisResult:
    """
    Sends raw extracted text to Gemini API and receives a structured JSON analysis.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY was not found in environment variables.")

    client = genai.Client(api_key=api_key)

    prompt = f"""
    Analyze the following raw text extracted from a web source:
    
    "{raw_text}"
    
    Provide a professional summary, determine the sentiment, and extract key entities.
    """

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=DataAnalysisResult,
            temperature=0.2,
        ),
    )

    return DataAnalysisResult.model_validate_json(response.text)
