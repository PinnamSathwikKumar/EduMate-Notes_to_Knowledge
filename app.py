#!/usr/bin/env python3
"""
Edumate - Offline Multilingual Document Summarizer
BTech Major Project (AI)
"""

import os
import re
import random
from pathlib import Path

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    AutoModelForQuestionAnswering
)
from sentence_transformers import SentenceTransformer
import pdfplumber
import PyPDF2
from docx import Document
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize


# -------------------- OFFLINE SAFETY --------------------
os.environ["TRANSFORMERS_OFFLINE"] = "1"
torch.set_num_threads(2)

#--------------------DEVICE---------------------------
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"🔥 Using device: {DEVICE}")
if DEVICE.type == "cuda":
    torch.backends.cudnn.benchmark = True


# -------------------- NLTK --------------------
NLTK_DATA_PATH = Path(__file__).parent / "nltk_data"
nltk.data.path.append(str(NLTK_DATA_PATH))

try:
    nltk.data.find("tokenizers/punkt")
    nltk.data.find("corpora/stopwords")
    print("✓ NLTK data found")
except LookupError:
    print("❌ NLTK data missing. Run once: python download_nltk.py")
# -------------------- APP --------------------
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------------------- GLOBAL MODELS --------------------
summarizer_model = None
summarizer_tokenizer = None
qa_model = None
qa_tokenizer = None
sentence_model = None
question_gen_model = None
question_gen_tokenizer = None
# Translation models
translator_hi_model = None
translator_hi_tokenizer = None
translator_te_model = None
translator_te_tokenizer = None
# Store the most recent uploaded document so all pages can reuse it
CURRENT_DOCUMENT = {"filename": None, "text": None}


# ======================================================
# MODEL LOADING
# ======================================================
def load_models():
    global summarizer_model, summarizer_tokenizer
    global qa_model, qa_tokenizer
    global sentence_model
    global translator_hi_model, translator_hi_tokenizer
    global translator_te_model, translator_te_tokenizer
    global question_gen_model, question_gen_tokenizer
    base = Path(__file__).parent / "models"

    print("🔄 Loading models (OFFLINE MODE)")

    # Summarizer 
    summarizer_tokenizer = AutoTokenizer.from_pretrained(
        base / "summarizer", local_files_only=True
    )
    summarizer_model = AutoModelForSeq2SeqLM.from_pretrained(
        base / "summarizer", local_files_only=True
    ).to(DEVICE).eval()
    print("✓ Summarizer loaded")

    # QA
    qa_tokenizer = AutoTokenizer.from_pretrained(
        base / "qa_model", local_files_only=True
    )
    qa_model = AutoModelForQuestionAnswering.from_pretrained(
        base / "qa_model", local_files_only=True
    ).to(DEVICE).eval()
    print("✓ QA model loaded")

    # Question Generator (Flan-T5)
    qg_path = base / "question_generator"

    question_gen_tokenizer = AutoTokenizer.from_pretrained(
        qg_path, local_files_only=True
    )

    question_gen_model = AutoModelForSeq2SeqLM.from_pretrained(
        qg_path, local_files_only=True
    ).to(DEVICE).eval()

    print("✓ Question Generator loaded (Flan-T5-Base)")

    # Sentence Embedder
    sentence_model = SentenceTransformer(
        str(base / "sentence_embedder"),
        device=str(DEVICE)
    )
    print("✓ Sentence embedder loaded")

    # Translation models (load if available)
    try:
        hi_path = base / "en-hi"
        if hi_path.exists() and (hi_path / "config.json").exists():
            translator_hi_tokenizer = AutoTokenizer.from_pretrained(
                str(hi_path), local_files_only=True
            )
            translator_hi_model = AutoModelForSeq2SeqLM.from_pretrained(
                str(hi_path), local_files_only=True
            ).to(DEVICE)
            # Set to evaluation mode for faster inference
            translator_hi_model.eval()
            print("✓ Hindi translator loaded ")
        else:
            print("⚠️  Hindi translator not found (optional)")
            print("   Run download_models.py to download: Helsinki-NLP/opus-mt-en-hi")
    except Exception as e:
        print(f"⚠️  Could not load Hindi translator: {e}")
        print("   Run download_models.py to download the model")

    try:
        te_path = base / "en-te"
        if te_path.exists() and (te_path / "config.json").exists():
            translator_te_tokenizer = AutoTokenizer.from_pretrained(
                str(te_path), local_files_only=True
            )
            translator_te_model = AutoModelForSeq2SeqLM.from_pretrained(
                str(te_path), local_files_only=True
            ).to(DEVICE)
            # Set to evaluation mode for faster inference
            translator_te_model.eval()
            print("✓ Telugu translator loaded (Meher2006/english-to-telugu-model)")
        else:
            print("⚠️  Telugu translator not found (optional)")
            print("   Run download_models.py to download: Meher2006/english-to-telugu-model")
    except Exception as e:
        print(f"⚠️  Could not load Telugu translator: {e}")
        print("   Run download_models.py to download the model")

    if torch.cuda.is_available():
        torch.cuda.empty_cache()


# ======================================================
# TEXT EXTRACTION
# ======================================================
def extract_text_from_file(path):
    ext = Path(path).suffix.lower()

    if ext == ".pdf":
        text = ""
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                if page.extract_text():
                    text += page.extract_text() + "\n"
        return text

    if ext == ".docx":
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)

    if ext == ".txt":
        return Path(path).read_text(encoding="utf-8")

    return ""


# ======================================================
# CHUNKING (KEY FIX)
# ======================================================
def chunk_text(text, max_words=850):
    words = text.split()
    chunks, current = [], []

    for w in words:
        current.append(w)
        if len(current) >= max_words:
            chunks.append(" ".join(current))
            current = []

    if current:
        chunks.append(" ".join(current))

    return chunks
def split_into_sentences(text):
    return re.split(r'(?<=[.!?])\s+', text)

# ======================================================
# SUMMARIZATION (OPTIMIZED)
# ======================================================
def filter_important_sentences(text, keep_ratio=0.45):
    if len(text.split()) < 800:
        return text

    try:
        sentences = nltk.sent_tokenize(text)
    except:
        sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s for s in sentences if len(s.split()) > 8]

    if len(sentences) < 10:
        return text

    embeddings = sentence_model.encode(sentences, show_progress_bar=False, batch_size=16)
    doc_embedding = embeddings.mean(axis=0)

    import numpy as np

    scores = [
        (s, float(np.dot(e, doc_embedding) /
                  (np.linalg.norm(e) * np.linalg.norm(doc_embedding))))
        for s, e in zip(sentences, embeddings)
    ]
    scores.sort(key=lambda x: x[1], reverse=True)

    keep = int(len(scores) * keep_ratio)
    selected = [s for s, _ in scores[:keep]]

    return " ".join(selected)

def summarize_large_text(text, summary_type="short"):
    """
    SMART DYNAMIC SUMMARIZATION
    - Output size proportional to input size
    - Real full-length summaries
    - Better chunk aggregation
    """
    # Reduce noise BEFORE summarization
    text = filter_important_sentences(text)

    total_words = len(text.split())

    # Dynamic percentage based system
    ratio_map = {
        "short": 0.25,      # 25% of original
        "detailed": 0.50,   # 50% of original
        "full": 0.80        # 80% of original
    }

    ratio = ratio_map.get(summary_type, 0.25)

    target_length = int(total_words * ratio)

    # Sensible boundaries
    target_length = max(120, target_length)
    target_length = min(1600, target_length)

    min_length = max(60, int(target_length * 0.40))


    # Adaptive chunking
    if total_words < 1200:
        chunk_size = 900
    elif total_words < 3000:
        chunk_size = 1100
    else:
        chunk_size = 1300

    chunks = chunk_text(text, max_words=chunk_size)
    per_chunk_length = min(600, max(250, target_length // len(chunks)))
    per_chunk_min = max(120, int(per_chunk_length * 0.6))


    summaries = []

    for chunk in chunks:
        if not chunk.strip():
            continue

        input_text = "Write a detailed academic summary explaining all major concepts clearly:\n\n" + chunk

        inputs = summarizer_tokenizer(
            input_text,
            max_length=1024,
            truncation=True,
            return_tensors="pt"
        ).to(DEVICE)

        with torch.no_grad():
            ids = summarizer_model.generate(
                inputs.input_ids,
                max_length=per_chunk_length,
                min_length=per_chunk_min,

                num_beams=2,
                length_penalty=0.9,      # encourage longer text
                early_stopping=False,    # allow full expansion

                no_repeat_ngram_size=3,
                repetition_penalty=1.1,

                do_sample=False
            )

        summary = summarizer_tokenizer.decode(
            ids[0], skip_special_tokens=True
        )

        summaries.append(summary)

    final_summary = " ".join(summaries)

    # Final trimming to exact target
    words = final_summary.split()

    return final_summary

# ======================================================
# TRANSLATION (OFFLINE - OPTIMIZED)
# ======================================================
def translate_text(text, target_lang="hi",target_words=None):
    """
    Translate text to Hindi or Telugu using offline models.
    Optimized for speed with efficient chunking and beam search.
    Returns original text if translation fails or model not available.
    """
    if target_lang == "hi":
        if translator_hi_model is None or translator_hi_tokenizer is None:
            return text

        try:
            sentences = split_into_sentences(text)
            translations = []

            for sentence in sentences:
                if not sentence.strip():
                    continue

                inputs = translator_hi_tokenizer(
                    sentence,
                    return_tensors="pt",
                    truncation=True,
                    max_length=256
                ).to(DEVICE)

                with torch.no_grad():
                    translated = translator_hi_model.generate(
                        inputs.input_ids,
                        max_length=256
                    )

                translated_text = translator_hi_tokenizer.decode(
                    translated[0],
                    skip_special_tokens=True
                )

                translations.append(translated_text)

            return " ".join(translations)

        except Exception as e:
            print("Translation error (Hindi):", e)
            return text
    
    elif target_lang == "te":
        if translator_te_model is None or translator_te_tokenizer is None:
            return text

        try:
            chunks = chunk_text(text, max_words=250)
            translations = []

            for chunk in chunks:
                if not chunk.strip():
                    continue

                inputs = translator_te_tokenizer(
                    chunk,
                    return_tensors="pt",
                    truncation=True,
                    max_length=512
                ).to(DEVICE)

                with torch.no_grad():
                    translated = translator_te_model.generate(
                        inputs.input_ids,
                        max_length=512
                    )

                translated_text = translator_te_tokenizer.decode(
                    translated[0],
                    skip_special_tokens=True
                )

                translations.append(translated_text)

            return " ".join(translations)

        except Exception as e:
            print(f"Translation error (Telugu): {e}")
            return text
        
    return text  # Return original for English or unknown languages


# ======================================================
# QA
# ======================================================
def answer_question(question, context):
    context = context[:1500]

    inputs = qa_tokenizer(
        question,
        context,
        truncation=True,
        max_length=512,
        return_tensors="pt"
    ).to(DEVICE)


    with torch.no_grad():
        out = qa_model(**inputs)

    start = torch.argmax(out.start_logits)
    end = torch.argmax(out.end_logits)

    if end < start:
        return "No answer found"

    end = end + 1

    ans = qa_tokenizer.decode(
        inputs.input_ids[0][start:end],
        skip_special_tokens=True
    )

    return ans if ans else "No answer found"


# ======================================================
# KEYWORDS
# ======================================================
def extract_keywords(text, k=10):
    # Simple frequency-based keyword extraction returning scored keywords
    text = re.sub(r"[^\w\s]", " ", text.lower())
    try:
        tokens = nltk.word_tokenize(text)
    except:
        tokens = text.split()
    stop = set(stopwords.words("english"))
    words = [w for w in tokens if w not in stop and len(w) > 2 and not w.isdigit()]

    if not words:
        return []

    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1

    # Normalize scores to 0..1 by dividing by max frequency
    max_f = max(freq.values())
    items = sorted(freq.items(), key=lambda x: x[1], reverse=True)

    keywords = []
    for w, count in items[:k]:
        keywords.append({
            "keyword": w,
            "score": round(count / max_f, 4),
            "frequency": count  # Add frequency count for sorting
        })

    return keywords

# ======================================================
# ROUTES (FIXED FOR UI)
# ======================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/summary")
def summary_page():
    return render_template("summary.html")


@app.route("/flashcards")
def flashcards_page():
    return render_template("flashcard.html")


@app.route("/keywords")
def keywords_page():
    return render_template("keywords.html")


@app.route("/privacy")
def privacy_page():
    return render_template("privacy.html")


@app.route("/terms")
def terms_page():
    return render_template("terms.html")

@app.route("/api/upload", methods=["POST"])
def api_upload():
    try:
        if "file" not in request.files:
            return jsonify(success=False, error="No file uploaded")

        file = request.files["file"]
        if file.filename == "":
            return jsonify(success=False, error="Empty filename")

        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)

        text = extract_text_from_file(path)

        if not text.strip():
            return jsonify(success=False, error="Could not extract text")

        # Save the extracted text for reuse across pages
        CURRENT_DOCUMENT["filename"] = file.filename
        CURRENT_DOCUMENT["text"] = text

        return jsonify(
            success=True,
            filename=file.filename,
            full_text=text
        )

    except Exception as e:
        print("❌ Upload error:", e)
        return jsonify(success=False, error=str(e))

@app.route("/api/summarize", methods=["POST"])
def api_summarize():
    try:
        data = request.get_json()

        text = data.get("text", "")
        summary_type = data.get("type", "short")
        language = data.get("language", "en")

        if not text.strip():
            return jsonify(success=False, error="No text provided")

        # Validate summary type
        if summary_type not in ["short", "detailed", "full"]:
            summary_type = "short"

        # Generate English summary first (always)
        print(f"📝 Generating {summary_type} summary in English...")
        import time
        start_time = time.time()
        
        summary = summarize_large_text(text, summary_type)
        target_words = len(summary.split())
        summary_time = time.time() - start_time
        print(f"✓ Summary generated in {summary_time:.2f}s")

        # Translate to target language if requested
        if language in ["hi", "te"]:
            lang_name = "Hindi" if language == "hi" else "Telugu"
            print(f"🌐 Translating summary to {lang_name}...")
            
            # Check if translator is available
            if language == "hi" and (translator_hi_model is None or translator_hi_tokenizer is None):
                return jsonify(
                    success=False,
                    error="Hindi translator model not loaded. Please run download_models.py to download the model."
                )
            elif language == "te" and (translator_te_model is None or translator_te_tokenizer is None):
                return jsonify(
                    success=False,
                    error="Telugu translator model not loaded. Please run download_models.py to download the model."
                )
            
            trans_start = time.time()
            translated_summary = translate_text(summary, target_lang=language, target_words=target_words)
            trans_time = time.time() - trans_start
            print(f"✓ Translation completed in {trans_time:.2f}s")
            
            # Verify translation didn't fail (check if it's different from original)
            if translated_summary and translated_summary != summary:
                summary = translated_summary
            else:
                print(f"⚠️  Translation may have failed, returning English summary")
                # Still return English summary rather than failing

        total_time = time.time() - start_time
        print(f"✓ Total processing time: {total_time:.2f}s")

        return jsonify(
            success=True,
            summary=summary,
            language=language,
            summary_type=summary_type
        )

    except Exception as e:
        print("❌ Summary error:", e)
        import traceback
        traceback.print_exc()
        return jsonify(success=False, error=str(e))
    
# ======================================================
# FLASHCARD GENERATION
# ======================================================
def generate_flashcards(text, num_flashcards=10, flashcard_type="qa"):
    """
    Generate flashcards from document text.
    Types: 'qa' (Question & Answer), 'mcq' (Multiple Choice), 'fill' (Fill in the Blanks)
    """
    
    if not text or not text.strip():
        return []
    
    # Split text into sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    
    if len(sentences) < num_flashcards:
        # If not enough sentences, chunk the text
        chunks = chunk_text(text, max_words=150)
        sentences = chunks[:num_flashcards * 2]  # Get more chunks than needed
    
    flashcards = []
    used_sentences = set()
    
    # Generate questions using Flan-T5 model
    attempts = 0
    max_attempts = num_flashcards * 3
    
    while len(flashcards) < num_flashcards and attempts < max_attempts:
        attempts += 1
        
        # Select a sentence/chunk that hasn't been used
        available = [s for s in sentences if s not in used_sentences and len(s.strip()) > 30]
        if not available:
            break
            
        context = random.choice(available)
        used_sentences.add(context)
        
        # Generate question using T5 model
        try:
            # Use Flan-T5 for question generation
            input_text = f"Generate one clear question from the text:\n\n{context[:300]}"

            inputs = question_gen_tokenizer(
                input_text,
                max_length=512,
                truncation=True,
                return_tensors="pt"
            ).to(DEVICE)

            with torch.no_grad():
                ids = question_gen_model.generate(
                    inputs.input_ids,
                    max_length=40,                # Shorter = cleaner
                    num_beams=3,                  # Keep low
                    do_sample=False,              # Deterministic
                    repetition_penalty=1.5,       # Strong repetition control
                    no_repeat_ngram_size=3,
                    early_stopping=True
                )
            
            question = question_gen_tokenizer.decode(
                ids[0],
                skip_special_tokens=True
            ).strip()

            # Clean up question
            question = question.replace("question:", "").strip()
            question = question.replace("Question:", "").strip()

            if not question.endswith("?"):
                question += "?"

            # --------- ADD THIS VALIDATION HERE ---------
            if len(question.split()) < 5:
                continue

            if any(char.isdigit() for char in question[:15]):
                continue
            # --------------------------------------------

            # Generate answer using QA model
            answer = answer_question(question, context)
            if not answer or answer == "No answer found" or len(answer.strip()) < 5:
                answer = context[:200].strip()
            
            if flashcard_type == "qa":
                flashcards.append({
                    "question": question,
                    "answer": answer
                })
            
            elif flashcard_type == "mcq":
                # Generate multiple choice options
                keywords = extract_keywords(context, k=15)
                correct_answer = answer[:100] if len(answer) > 100 else answer
                options = [correct_answer]
                
                # Add distractors from keywords and other sentences
                distractors = []
                
                # Use keywords as distractors
                for kw in keywords[:5]:
                    kw_text = kw["keyword"].capitalize()
                    if kw_text.lower() not in correct_answer.lower() and len(kw_text) > 3:
                        distractors.append(kw_text)
                
                # Add short phrases from other sentences as distractors
                other_sentences = [s for s in sentences if s != context and len(s) > 30][:10]
                for sent in other_sentences[:3]:
                    words = sent.split()[:8]
                    if words:
                        phrase = " ".join(words)
                        if phrase.lower() not in correct_answer.lower():
                            distractors.append(phrase)
                
                # Ensure we have at least 3 distractors
                while len(distractors) < 3 and len(other_sentences) > 0:
                    sent = other_sentences.pop(0) if other_sentences else ""
                    if sent:
                        distractors.append(sent[:50])
                
                # Combine options and shuffle
                options.extend(distractors[:3])
                random.shuffle(options)
                
                # Find correct index after shuffle
                correct_index = next(i for i, opt in enumerate(options) if opt == correct_answer)
                
                flashcards.append({
                    "question": question,
                    "options": options[:4],  # Limit to 4 options
                    "correct_answer": correct_index,
                    "answer": answer
                })
            
            elif flashcard_type == "fill":
                # Create fill-in-the-blank question
                # Find a key word or phrase to blank out
                words = answer.split() if answer else context.split()
                
                if len(words) >= 3:
                    # Try to find a meaningful word (not common words)
                    common_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "can", "this", "that", "these", "those", "it", "its", "they", "them", "their"}
                    
                    # Find a good word to blank (prefer nouns/adjectives)
                    key_word = None
                    for i in range(len(words) // 2, len(words)):
                        word = words[i].strip(".,!?;:")
                        if len(word) > 4 and word.lower() not in common_words:
                            key_word = word
                            break
                    
                    if not key_word and len(words) > 0:
                        key_word = words[len(words) // 2].strip(".,!?;:")
                    
                    if key_word:
                        question_with_blanks = re.sub(
                            r'\b' + re.escape(key_word) + r'\b',
                            "_____",
                            context,
                            count=1
                        )

                        flashcards.append({
                            "question": f"Fill in the blank: {question_with_blanks[:300]}",
                            "question_with_blanks": question_with_blanks[:300],
                            "answer": key_word
                        })
                    else:
                        # Fallback to Q&A format
                        flashcards.append({
                            "question": question,
                            "question_with_blanks": context[:300],
                            "answer": answer
                        })
                else:
                    flashcards.append({
                        "question": question,
                        "question_with_blanks": context[:300],
                        "answer": answer
                    })
        
        except Exception as e:
            print(f"Error generating flashcard {len(flashcards) + 1}: {e}")
            # Fallback: simple Q&A
            if context:
                flashcards.append({
                    "question": f"What is mentioned about: {context[:100]}?",
                    "answer": context[:200] if len(context) > 200 else context
                })
    
    return flashcards


@app.route("/api/flashcards", methods=["POST"])
def api_flashcards():
    try:
        data = request.get_json()
        text = data.get("text", "")
        num_flashcards = int(data.get("num_flashcards", 10))
        flashcard_type = data.get("flashcard_type", "qa")

        # Use current document if text not provided
        if not text.strip() and CURRENT_DOCUMENT.get("text"):
            text = CURRENT_DOCUMENT["text"]

        if not text.strip():
            return jsonify(success=False, error="No text provided. Please upload a document first.")

        flashcards = generate_flashcards(text, num_flashcards, flashcard_type)

        if not flashcards:
            return jsonify(success=False, error="Could not generate flashcards. Please try with a different document or fewer flashcards.")

        return jsonify(
            success=True,
            flashcards=flashcards
        )

    except Exception as e:
        print("❌ Flashcard generation error:", e)
        import traceback
        traceback.print_exc()
        return jsonify(success=False, error=str(e))

@app.route("/api/keywords", methods=["POST"])
def api_keywords():
    try:
        data = request.get_json()
        text = data.get("text", "")

        if not text.strip():
            return jsonify(success=False, error="No text provided")

        num_keywords = int(data.get("num_keywords", 10) or 10)

        keywords = extract_keywords(text, k=num_keywords)

        return jsonify(success=True, keywords=keywords)

    except Exception as e:
        print("❌ Keywords error:", e)
        return jsonify(success=False, error=str(e))


@app.route("/api/current_document", methods=["GET"])
def api_current_document():
    try:
        if CURRENT_DOCUMENT.get("filename") and CURRENT_DOCUMENT.get("text"):
            return jsonify(
                success=True,
                filename=CURRENT_DOCUMENT["filename"],
                full_text=CURRENT_DOCUMENT["text"],
            )

        return jsonify(success=False, filename=None, full_text=None)
    except Exception as e:
        print("❌ Current document error:", e)
        return jsonify(success=False, error=str(e))


@app.route("/api/clear_document", methods=["POST"])
def api_clear_document():
    try:
        filename = CURRENT_DOCUMENT.get("filename")
        # Clear in-memory record
        CURRENT_DOCUMENT["filename"] = None
        CURRENT_DOCUMENT["text"] = None

        # Remove stored file if exists
        if filename:
            path = os.path.join(UPLOAD_FOLDER, filename)
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass

        return jsonify(success=True)
    except Exception as e:
        print("❌ Clear document error:", e)
        return jsonify(success=False, error=str(e))

# ======================================================
# MAIN
# ======================================================
if __name__ == "__main__":
    print("🔄 Starting Edumate...")
    print("⏳ Loading ML models...")
    try:
        load_models()
        print("✅ All models loaded successfully!")
        print("🚀 Edumate running at http://localhost:5000")
        app.run(host="0.0.0.0", port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n⚠️  Startup interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during startup: {e}")
        import traceback
        traceback.print_exc()

