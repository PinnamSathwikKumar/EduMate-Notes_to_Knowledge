#!/usr/bin/env python3
"""
Model Verification Script - Check if all required models are downloaded
"""

from pathlib import Path

BASE = Path(__file__).parent
MODELS = BASE / "models"


def check_model(model_name, model_path):
    """Check if a model exists and has required files"""
    path = MODELS / model_path

    # Basic files that every transformer model must contain
    required_files = ["config.json"]

    if not path.exists():
        return False, f"Directory not found: {model_path}"

    missing_files = []
    for file in required_files:
        if not (path / file).exists():
            missing_files.append(file)

    if missing_files:
        return False, f"Missing files: {', '.join(missing_files)}"

    return True, "OK"


def main():
    print("🔍 Verifying Models for Offline Operation\n")

    models_to_check = {
        "Summarizer ": "summarizer",
        "QA Model": "qa_model",
        "Sentence Embedder": "sentence_embedder",
        "Hindi Translator": "en-hi",
        "Telugu Translator": "en-te"
    }

    all_ok = True

    for name, path in models_to_check.items():
        status, message = check_model(name, path)

        if status:
            print(f"✅ {name}: {message}")
        else:
            print(f"❌ {name}: {message}")
            all_ok = False

    print("\n" + "=" * 50)

    if all_ok:
        print("✅ All models are downloaded and ready for offline operation!")
    else:
        print("⚠️ Some models are missing. Run download_models.py to download them.")


if __name__ == "__main__":
    main()
