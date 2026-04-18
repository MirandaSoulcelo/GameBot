import spacy
import numpy as np
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from langdetect import detect, detect_langs
from nltk.corpus import stopwords
import nltk

nltk.download('stopwords', quiet=True)

STOPWORDS_PT = set(stopwords.words("portuguese"))
STOPWORDS_EN = set(stopwords.words("english"))


class NLPEngine:

    def __init__(self):
        print("Inicializando motor NLP...")

        self.nlp_en = spacy.load("en_core_web_lg")
        self.nlp_pt = spacy.load("pt_core_news_lg")

        self.kb_en = self.load_knowledge_base("en")
        self.kb_pt = self.load_knowledge_base("pt")

        self.all_blocks_en = self._flatten(self.kb_en)
        self.all_blocks_pt = self._flatten(self.kb_pt)

        print("Motor NLP pronto!\n")

    def load_knowledge_base(self, language):
        file = f"knowledge_base_{language}.json"
        with open(file, "r", encoding="utf-8") as f:
            kb = json.load(f)
        total = sum(len(v) for v in kb.values())
        print(f"Base {language} carregada — {total} blocos")
        return kb

    def _flatten(self, kb):

        blocks = []
        for intent_blocks in kb.values():
            blocks.extend(intent_blocks)
        return blocks

    def preprocessing(self, sentence, language):

        nlp = self.nlp_pt if language == "pt" else self.nlp_en

        doc = nlp(sentence.lower())

        tokens = [
            token.lemma_
            for token in doc
            if not token.is_punct
            and not token.is_space
            and not token.like_num
            and len(token.text) > 1
            and not token.is_stop
        ]

        entities = [ent.text.lower() for ent in doc.ents]

        all_tokens = list(set(tokens + entities))
        return " ".join(all_tokens)

    def detect_language(self, text, default_language):
        if len(text.split()) < 2:
            return default_language
        try:
            results = detect_langs(text)
            best = results[0]
            if str(best.lang) in ["en", "pt"] and best.prob > 0.85:
                return str(best.lang)
        except Exception:
            pass
        return default_language

    def detect_intent(self, text, language):
        t = text.lower()

        intents_pt = {
            "personagens":   ["quem é", "quem foi", "personagem", "protagonista", "vilão", "herói", "mascote"],
            "empresas":      ["empresa", "desenvolvedora", "quem criou", "quem desenvolveu", "quem publicou"],
            "franquias":     ["franquia", "série", "saga"],
            "jogos":         ["quais jogos", "lista de jogos", "jogos de", "lançamentos", "jogo lançado"],
            "gameplay":      ["gameplay", "jogabilidade", "como joga", "como funciona", "mecânicas"],
            "historia_lore": ["história", "lore", "enredo", "historia de", "qual a história"],
            "habilidades":   ["poder", "habilidade", "ataques", "skills", "golpe"],
            "mundo_universo":["universo", "mundo", "reino", "onde se passa"],
            "crossovers":    ["crossover", "aparece em", "participa de"],
        }

        intents_en = {
            "personagens":   ["who is", "character", "protagonist", "villain", "hero"],
            "empresas":      ["company", "developer", "publisher", "who created"],
            "franquias":     ["franchise", "series", "saga"],
            "jogos":         ["games", "game list", "released", "titles"],
            "gameplay":      ["gameplay", "how to play", "mechanics", "controls"],
            "historia_lore": ["story", "lore", "plot", "narrative"],
            "habilidades":   ["powers", "abilities", "skills", "moves", "attacks"],
            "mundo_universo":["world", "universe", "kingdom", "region"],
            "crossovers":    ["crossover", "appears in", "guest"],
        }

        intents = intents_pt if language == "pt" else intents_en

        for intent, keywords in intents.items():
            for kw in keywords:
                if kw in t:
                    return intent
                
        if len(t.split()) <= 3:
            return "personagens"

        return "curiosidades"

    def extract_entities(self, text, language):
        nlp = self.nlp_pt if language == "pt" else self.nlp_en
        doc = nlp(text)
        return [ent.text.lower() for ent in doc.ents]

    def is_too_similar(self, sent_a, sent_b, language):

        nlp = self.nlp_pt if language == "pt" else self.nlp_en
        doc_a = nlp(sent_a)
        doc_b = nlp(sent_b)
        if doc_a.vector_norm and doc_b.vector_norm:
            return doc_a.similarity(doc_b) > 0.85
        return False

    def answer(self, user_text, threshold=0.15, top_k=3, default_language="pt"):

        language = self.detect_language(user_text, default_language)
        intent   = self.detect_intent(user_text, language)
        nlp      = self.nlp_pt if language == "pt" else self.nlp_en

        all_blocks = self.all_blocks_pt if language == "pt" else self.all_blocks_en

        no_answer = (
            "Desculpe, não encontrei respostas relevantes sobre isso."
            if language == "pt"
            else "Sorry, I couldn't find relevant answers about that."
        )

        print(f"[DEBUG] idioma={language} | intenção={intent}")

        entities = self.extract_entities(user_text, language)

        if not entities:
            sw = STOPWORDS_PT if language == "pt" else STOPWORDS_EN
            entities = [w for w in user_text.lower().split() if w not in sw and len(w) > 2]

        print(f"[DEBUG] entidades={entities}")

        filtered = [
            b for b in all_blocks
            if any(e in b["text"].lower() for e in entities)
        ]

        if len(filtered) < 5:
            filtered = [b for b in all_blocks if b["intent"] == intent]

        if len(filtered) < 5:
            filtered = all_blocks

        if not filtered:
            return no_answer, "video game"

        sentences_pool = [b["text"]  for b in filtered]
        topics_pool    = [b["topic"] for b in filtered]

        cleaned_pool = [self.preprocessing(s, language) for s in sentences_pool]
        user_clean   = self.preprocessing(user_text, language)

        vectorizer  = TfidfVectorizer()
        all_vectors = vectorizer.fit_transform(cleaned_pool + [user_clean])

        tfidf_scores = cosine_similarity(
            all_vectors[-1],   
            all_vectors[:-1]  
        )[0]

        user_doc     = nlp(user_text)
        spacy_scores = []

        for s in sentences_pool:
            s_doc = nlp(s)
            if user_doc.vector_norm and s_doc.vector_norm:
                spacy_scores.append(user_doc.similarity(s_doc))
            else:
                spacy_scores.append(0.0)

        spacy_scores = np.array(spacy_scores)

        combined = 0.7 * tfidf_scores + 0.3 * spacy_scores

        for i, s in enumerate(sentences_pool):
            if any(e in s.lower() for e in entities):
                combined[i] *= 2.0

        sorted_idx = combined.argsort()[::-1]
        best_sentences = []
        results        = []

        for idx in sorted_idx:
            candidate = sentences_pool[idx]

            if any(self.is_too_similar(candidate, c, language) for c in best_sentences):
                continue

            best_sentences.append(candidate)

            results.append(
                f"📌 {topics_pool[idx]}\n{candidate}"
            )

            if len(results) == top_k:
                break

        if not results or combined[sorted_idx[0]] < threshold:
            return no_answer, "video game"

        best_topic = topics_pool[sorted_idx[0]]
        return "\n\n".join(results), best_topic