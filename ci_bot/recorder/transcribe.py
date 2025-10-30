# recorder/transcribe.py
import wave, json, os
from vosk import Model, KaldiRecognizer
import pathlib

ROOT = pathlib.Path(__file__).parent
VOSK_MODEL = os.environ.get("VOSK_MODEL_PATH", str(ROOT.parent / "backend" / "models" / "vosk-model-small-en-us-0.15"))

if not os.path.exists(VOSK_MODEL):
    raise RuntimeError(f"Vosk model not found at {VOSK_MODEL}; set VOSK_MODEL_PATH or place model under backend/models/...")

model = Model(VOSK_MODEL)

# small NLP using spaCy + transformers
import spacy
from transformers import pipeline
nlp_spacy = None
sentiment = None
try:
    nlp_spacy = spacy.load("en_core_web_sm")
except Exception:
    nlp_spacy = spacy.blank("en")
try:
    sentiment = pipeline("sentiment-analysis")
except Exception:
    sentiment = None

def transcribe_vosk(wav_path):
    wf = wave.open(wav_path, "rb")
    rec = KaldiRecognizer(model, wf.getframerate())
    texts = []
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            res = rec.Result()
            try:
                texts.append(json.loads(res).get("text",""))
            except:
                pass
    final = rec.FinalResult()
    try:
        texts.append(json.loads(final).get("text",""))
    except:
        pass
    return " ".join(t for t in texts if t)

def analyze_text(text):
    doc = nlp_spacy(text)
    ents = [{"text":e.text,"label":e.label_} for e in doc.ents]
    # simple competitor detection
    COMPETITORS = ["salesforce","hubspot","zoho","oracle","microsoft","sap"]
    comps = [c for c in COMPETITORS if c in text.lower()]
    obj_keywords = ["budget","price","pricing","cost","expensive","afford"]
    objections = [k for k in obj_keywords if k in text.lower()]
    sent = None
    if sentiment:
        try:
            sent = sentiment(text[:1000])[0]
        except:
            sent = None
    return {"transcript": text, "entities": ents, "competitors": comps, "objections": objections, "sentiment": sent}

def transcribe_and_analyze(wav_path):
    text = transcribe_vosk(wav_path)
    analysis = analyze_text(text)
    return analysis
