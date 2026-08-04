import os
import google.generativeai as genai
from app.models import DataAnalysisResult


def analyze_content_with_gemini(raw_text: str) -> DataAnalysisResult:
    """
    Sends raw extracted text to Gemini API and receives a structured JSON analysis.
    """
    # Configure the client with the API key from environment variables
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY was not found in environment variables.")
    genai.configure(api_key=api_key)

    prompt = f"""
    Analyze the following raw text extracted from a web source:
    
    "{raw_text}"
    
    Provide a professional summary, determine the sentiment, and extract key entities.
    """

    # Use the configured generative model
    model = genai.GenerativeModel("gemini-1.5-flash-latest")
    response = model.generate_content(
        contents=prompt,
        generation_config=genai.types.GenerationConfig(
            response_mime_type="application/json",
            response_schema=DataAnalysisResult,
            temperature=0.2,
        ),
    )

    return DataAnalysisResult.model_validate_json(response.text)
