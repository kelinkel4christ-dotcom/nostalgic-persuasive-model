"""
Emotion Detection using fine-tuned DistilRoBERTa model.

This module provides emotion prediction from text input using a
multi-label classification model trained on the Cirimus/Super-Emotion dataset.
"""

from typing import Any, Dict

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


class EmotionDetector:
    """Emotion detection using a fine-tuned DistilRoBERTa model."""

    LABELS = ["anger", "fear", "joy", "love", "neutral", "sadness", "surprise"]
    THRESHOLD = 0.56  # Optimized threshold from training analysis

    def __init__(self, use_mock: bool = False) -> None:
        """
        Initialize the emotion detector. Requires HF_REPO_ID environment variable.

        Args:
            use_mock: If True, use a mock implementation (no model loading).
        """
        self.use_mock = use_mock
        if use_mock:
            print("   ⚠️ EmotionDetector initialized in MOCK mode.")
            return

        import os

        repo_id = os.getenv("HF_REPO_ID")

        if not repo_id:
            raise ValueError("HF_REPO_ID environment variable must be set")

        print(
            f"   Loading tokenizer from HF Hub: {repo_id} (subfolder=emotion_model)..."
        )
        self.tokenizer = AutoTokenizer.from_pretrained(
            repo_id, subfolder="emotion_model"
        )

        print(f"   Loading model from HF Hub: {repo_id} (subfolder=emotion_model)...")
        self.model = AutoModelForSequenceClassification.from_pretrained(
            repo_id, subfolder="emotion_model"
        )

        self.model.eval()

        # Use GPU if available
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        print(f"   Model loaded on device: {self.device}")

    def predict(self, text: str) -> Dict[str, Any]:
        """
        Predict emotion from text.

        Args:
            text: Input text to analyze.

        Returns:
            Dictionary containing:
                - emotion: The dominant emotion label (str)
                - confidence: Score of the dominant emotion (float)
                - probabilities: Dictionary of all emotion scores (dict[str, float])
        """
        if self.use_mock:
            return {
                "emotion": "neutral",
                "confidence": 0.5,
                "probabilities": {label: 0.1 for label in self.LABELS},
            }

        # Tokenize input
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        )

        # Move to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Run inference
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits

        # Apply sigmoid to get multi-label probabilities
        # (Model was trained with BCEWithLogitsLoss for multi-label)
        probabilities = torch.sigmoid(logits).cpu().numpy()[0]

        # Create probability dictionary
        prob_dict = {
            label: float(score) for label, score in zip(self.LABELS, probabilities)
        }

        # Determine dominant emotion based on threshold
        # We pick the highest score that exceeds threshold, or just highest if none do
        # Or simply argmax?
        # The notebook used: y_pred_new = (probs > THRESHOLD).astype(int)
        # But for a single label return, we usually want the *best* one.

        # Strategy:
        # 1. Filter by threshold
        # 2. If valid candidates, pick max
        # 3. If no valid candidates, pick "neutral" or max (fallback)

        valid_emotions = {k: v for k, v in prob_dict.items() if v >= self.THRESHOLD}

        if valid_emotions:
            dominant_emotion, confidence = max(
                valid_emotions.items(), key=lambda x: x[1]
            )
        else:
            dominant_emotion, confidence = max(prob_dict.items(), key=lambda x: x[1])

        return {
            "emotion": dominant_emotion,
            "confidence": confidence,
            "probabilities": prob_dict,
        }

    def close(self) -> None:
        """Clean up resources."""
        if self.use_mock:
            return

        # Clear model from memory
        del self.model
        del self.tokenizer
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
