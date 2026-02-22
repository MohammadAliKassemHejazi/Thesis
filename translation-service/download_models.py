# download_models.py
from transformers import MarianMTModel, MarianTokenizer

models = [
    "Helsinki-NLP/opus-mt-en-es",
    "Helsinki-NLP/opus-mt-en-fr",
    "Helsinki-NLP/opus-mt-en-de",
]

for m in models:
    print(f"Downloading {m}...", flush=True)
    MarianTokenizer.from_pretrained(m)
    MarianMTModel.from_pretrained(m)
    print(f"Done: {m}", flush=True)