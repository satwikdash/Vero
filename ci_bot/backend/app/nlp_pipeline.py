import spacy
from transformers import pipeline

nlp = spacy.load("en_core_web_sm")
sentiment_model = pipeline("sentiment-analysis")

def analyze_text(text):
    doc = nlp(text)
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    sentiment = sentiment_model(text[:512])[0]
    keywords = [chunk.text for chunk in doc.noun_chunks]

    insights = {
        "entities": entities,
        "sentiment": sentiment,
        "keywords": keywords
    }
    return insights
