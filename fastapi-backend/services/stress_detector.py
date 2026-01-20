"""
Stress Detection using fine-tuned RoBERTa model.

This module provides stress level prediction from text input
using a RoBERTa model fine-tuned for mental health stress detection.
"""

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


class StressDetector:
    """Stress detection using a fine-tuned RoBERTa model."""

    def __init__(self) -> None:
        """Initialize the stress detector. Requires HF_REPO_ID environment variable."""
        import os

        repo_id = os.getenv("HF_REPO_ID")

        if not repo_id:
            raise ValueError("HF_REPO_ID environment variable must be set")

        print(
            f"   Loading tokenizer from HF Hub: {repo_id} (subfolder=stress_detection_mental_roberta)..."
        )
        self.tokenizer = AutoTokenizer.from_pretrained(
            repo_id, subfolder="stress_detection_mental_roberta"
        )

        print(
            f"   Loading model from HF Hub: {repo_id} (subfolder=stress_detection_mental_roberta)..."
        )
        self.model = AutoModelForSequenceClassification.from_pretrained(
            repo_id, subfolder="stress_detection_mental_roberta"
        )

        self.model.eval()

        # Use GPU if available
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        print(f"   Model loaded on device: {self.device}")

    def predict(self, text: str) -> float:
        """
        Predict stress level from text.

        Args:
            text: Input text to analyze.

        Returns:
            Stress score between 0 (no stress) and 1 (high stress).
        """
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

        # Apply softmax to get probabilities
        probabilities = torch.softmax(logits, dim=-1)

        # Assuming label 1 is "stressed" and label 0 is "not stressed"
        # Return the probability of the "stressed" class
        stress_score = probabilities[0, 1].item()

        return stress_score

    def close(self) -> None:
        """Clean up resources."""
        # Clear model from memory
        del self.model
        del self.tokenizer
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
