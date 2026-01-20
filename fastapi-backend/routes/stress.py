"""
Text Analysis API Routes.

This module provides endpoints for text analysis including:
- Stress detection
- Emotion classification
"""

from fastapi import APIRouter, HTTPException, Request

from core.schemas import (
    EmotionResult,
    StressDetectionRequest,
    StressDetectionResponse,
    TextAnalysisRequest,
    TextAnalysisResponse,
)


router = APIRouter(prefix="/analyze", tags=["Text Analysis"])


@router.post(
    "/text",
    response_model=TextAnalysisResponse,
    summary="Analyze text for stress and emotion",
    description="Analyze text and return both stress level and detected emotion.",
)
async def analyze_text(
    request: Request,
    body: TextAnalysisRequest,
) -> TextAnalysisResponse:
    """
    Analyze text for stress level and emotion.

    Returns:
        - stress_score: 0 (no stress) to 1 (high stress)
        - emotion: detected emotion with confidence and probabilities
    """
    stress_detector = request.app.state.recommenders.get("stress")
    emotion_detector = request.app.state.recommenders.get("emotion")

    # Get stress prediction
    stress_score = 0.5  # Default if model not loaded
    if stress_detector is not None:
        try:
            stress_score = stress_detector.predict(body.text)
        except Exception as e:
            print(f"Error during stress prediction: {e}")

    # Get emotion prediction
    emotion_result = {
        "emotion": "neutral",
        "confidence": 0.5,
        "probabilities": {
            "anger": 0.1,
            "fear": 0.1,
            "joy": 0.1,
            "love": 0.1,
            "neutral": 0.5,
            "sadness": 0.05,
            "surprise": 0.05,
        },
    }
    if emotion_detector is not None:
        try:
            emotion_result = emotion_detector.predict(body.text)
        except Exception as e:
            print(f"Error during emotion prediction: {e}")

    return TextAnalysisResponse(
        text=body.text,
        stress_score=stress_score,
        emotion=EmotionResult(
            emotion=emotion_result["emotion"],
            confidence=emotion_result["confidence"],
            probabilities=emotion_result["probabilities"],
        ),
    )


# Legacy endpoint for backwards compatibility
@router.post(
    "/stress",
    response_model=StressDetectionResponse,
    summary="Predict stress level (legacy)",
    description="Analyze text and return a stress score between 0 (no stress) and 1 (high stress).",
    deprecated=True,
)
async def predict_stress(
    request: Request,
    body: StressDetectionRequest,
) -> StressDetectionResponse:
    """
    Predict stress level from text input.

    This endpoint is deprecated. Use /analyze/text instead.
    """
    detector = request.app.state.recommenders.get("stress")

    if detector is None:
        raise HTTPException(
            status_code=503,
            detail="Stress detection model is not loaded. Please try again later.",
        )

    try:
        stress_score = detector.predict(body.text)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during stress prediction: {str(e)}",
        )

    return StressDetectionResponse(
        stress_score=stress_score,
        text=body.text,
    )
