#!/usr/bin/env python3
"""
Edumate - Model Downloader (FAST + OFFLINE + MULTILINGUAL)
"""

import os
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForQuestionAnswering
from sentence_transformers import SentenceTransformer

BASE = Path(__file__).parent
MODELS = BASE / "models"


def _hf_auth_kwargs():
    """
    Return kwargs for Hugging Face auth if a token is available.
    """
    token = os.environ.get("HUGGINGFACE_TOKEN")
    if not token:
        return {}

    return {
        "token": token,
    }


def ensure_dirs():
    for d in [
        MODELS / "summarizer",
        MODELS / "qa_model",
        MODELS / "question_generator",
        MODELS / "sentence_embedder",
        MODELS / "en-hi",
        MODELS / "en-te",
    ]:
        d.mkdir(parents=True, exist_ok=True)


def download_summarizer():
    print("📥 Downloading summarizer ")
    model = "sshleifer/distilbart-cnn-12-6"
    kwargs = _hf_auth_kwargs()

    tok = AutoTokenizer.from_pretrained(model, **kwargs)
    mdl = AutoModelForSeq2SeqLM.from_pretrained(model, **kwargs)

    tok.save_pretrained(MODELS / "summarizer")
    mdl.save_pretrained(MODELS / "summarizer")


def download_translators():
    """
    Download translation models used by the app.
    """
    translators = {
        "en-hi": "Helsinki-NLP/opus-mt-en-hi",
        "en-te": "Meher2006/english-to-telugu-model",
    }

    hf_kwargs = _hf_auth_kwargs()

    for lang, model_name in translators.items():
        lang_name = "Hindi" if lang == "en-hi" else "Telugu"
        print(f"\n📥 Downloading {lang_name} translator → {model_name}")

        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name, **hf_kwargs)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name, **hf_kwargs)

            save_path = MODELS / lang
            save_path.mkdir(parents=True, exist_ok=True)

            tokenizer.save_pretrained(save_path)
            model.save_pretrained(save_path)

            print(f"✅ {lang_name} translator saved to {save_path}")

        except Exception as e:
            print(f"❌ Error downloading {lang_name} translator: {e}")


def download_qa():
    print("📥 Downloading QA model")
    m = "deepset/roberta-base-squad2"
    kwargs = _hf_auth_kwargs()

    tok = AutoTokenizer.from_pretrained(m, **kwargs)
    mdl = AutoModelForQuestionAnswering.from_pretrained(m, **kwargs)

    tok.save_pretrained(MODELS / "qa_model")
    mdl.save_pretrained(MODELS / "qa_model")

def download_question_generator():
    print("📥 Downloading Question Generator (Flan-T5-Base)")
    model_name = "google/flan-t5-base"
    kwargs = _hf_auth_kwargs()

    tok = AutoTokenizer.from_pretrained(model_name, **kwargs)
    mdl = AutoModelForSeq2SeqLM.from_pretrained(model_name, **kwargs)

    tok.save_pretrained(MODELS / "question_generator")
    mdl.save_pretrained(MODELS / "question_generator")

    

def download_sentence_embedder():
    print("📥 Downloading sentence embedder")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    save_path = MODELS / "sentence_embedder"
    save_path.mkdir(parents=True, exist_ok=True)

    model.save(str(save_path))


def main():
    ensure_dirs()
    download_summarizer()
    download_question_generator()
    download_qa()
    download_translators()
    download_sentence_embedder()

    print("\n🎉 ALL REQUIRED MODELS READY (OFFLINE MODE ENABLED)")


if __name__ == "__main__":
    main()
