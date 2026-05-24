from transformers import pipeline

classifier = pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-xlm-roberta-base-sentiment"
)

def analyze_sentiment(text):
    result = classifier(text)[0]

    label = result["label"].lower()

    if label not in ("positive", "negative", "neutral"):
        label = "neutral"

    return {
        "label": label,
        "score": float(result["score"])
    }