import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from services.emotion_detector import EmotionDetector


def test_emotion_detector():
    """Test EmotionDetector with sample inputs."""
    print("Testing EmotionDetector Integration...")

    # Path to model (adjusting for test script location)
    # test/ is inside fastapi-backend, so we go up one more level to find models
    model_path = Path(__file__).parent.parent.parent / "models" / "emotion_model"

    print(f"Model path: {model_path}")

    try:
        detector = EmotionDetector(model_path, use_mock=False)
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return

    test_sentences = [
        "I am so happy and excited about this!",
        "This is absolutely terrible and I hate it.",
        "I'm mostly indifferent about the whole situation.",
        "Wow, I didn't see that coming at all!",
        "I am feeling very anxious about the presentation.",
    ]

    print("\nRunning predictions:")
    for text in test_sentences:
        print(f"\nScanning: '{text}'")
        try:
            result = detector.predict(text)
            print(
                f"   -> Detected: {result['emotion'].upper()} (Confidence: {result['confidence']:.4f})"
            )
            # print(f"   -> Probs: {result['probabilities']}")
        except Exception as e:
            print(f"   ❌ Prediction failed: {e}")

    detector.close()
    print("\n✅ Test Complete.")


if __name__ == "__main__":
    test_emotion_detector()
