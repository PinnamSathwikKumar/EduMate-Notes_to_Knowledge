import nltk
from pathlib import Path

NLTK_DATA_PATH = Path(__file__).parent / "nltk_data"

print("Downloading NLTK data...")
nltk.download("punkt", download_dir=str(NLTK_DATA_PATH))
nltk.download("stopwords", download_dir=str(NLTK_DATA_PATH))
print("Done!")