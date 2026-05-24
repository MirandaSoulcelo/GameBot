import spacy
import numpy as np
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from langdetect import detect, detect_langs
from nltk.corpus import stopwords
import nltk
import re
from dictConfig import FRANCHISE_HINTS

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
        self.game_map = self.load_game_map()
        self.topic_map = self.build_topic_map()

        topics_kh = set(
            b["topic"] for b in self.all_blocks_en 
            if "kingdom hearts" in b["text"].lower() or "kingdom hearts" in b["topic"].lower()
        )
        print(f"[DEBUG KH TOPICS] {topics_kh}")

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

        entity_texts = {ent.start: ent.text.lower() for ent in doc.ents}

        tokens = []
        for token in doc:
            if token.i in entity_texts:
                tokens.append(entity_texts[token.i])  # nome próprio: sem lema
            elif (
                not token.is_punct
                and not token.is_space
                and not token.like_num
                and len(token.text) > 1
                and not token.is_stop
            ):
                tokens.append(token.lemma_)

        multi = [ent.text.lower() for ent in doc.ents if len(ent.text.split()) > 1]

        return " ".join(list(dict.fromkeys(tokens + multi)))

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
            "jogos": ["quais jogos", "lista de jogos", "jogos de", "lançamentos", "jogo lançado",
                      "jogo do", "jogo da", "sobre o jogo", "falar do jogo"],
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

    def answer(self, user_text, threshold=0.40, top_k=3, default_language="pt"):

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

        entities = [re.sub(r'[^\w\s]', '', e).lower().strip() for e in entities]
        entities = [e for e in entities if e]
        sw = STOPWORDS_PT if language == "pt" else STOPWORDS_EN
        
        if not entities:
            entities = [w for w in user_text.split() if w[0].isupper() and w.lower() not in sw]
        
        if not entities:
            entities = [w.lower() for w in user_text.split() if w.lower() not in sw and len(w) > 2]

        if not entities:
            entities = [w for w in user_text.lower().split() if len(w) > 1]

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
            return no_answer, "video game", []


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
            return no_answer, "video game", []
        

        best_topic = topics_pool[sorted_idx[0]]
        print(f"[DEBUG] best_topic={best_topic}")
        full_response = "\n\n".join(results)

        best_score = combined[sorted_idx[0]]
        top_blocks = [
            filtered[idx] for idx in sorted_idx
            if combined[idx] >= max(threshold, best_score * 0.75)
        ][:top_k]
    
        games = self.find_related_game(entities, top_blocks, language)

        if games:
            if language == "pt":
                lines = [f"  • {g['name']} ({g['platform']}) → {g['url']}" for g in games]
                full_response += "\n\n🎮 Quer jogar? Confira os jogos disponíveis:\n" + "\n".join(lines)
            else:
                lines = [f"  • {g['name']} ({g['platform']}) → {g['url']}" for g in games]
                full_response += "\n\n🎮 Want to play? Check available games:\n" + "\n".join(lines)

        return full_response, best_topic, entities

    
    def load_game_map(self):
        with open("game_map.json", "r", encoding="utf-8") as f:
            game_map = json.load(f)


        try:
            import requests as req
            tunnels = req.get("http://127.0.0.1:4040/api/tunnels", timeout=3).json()
            base_url = tunnels["tunnels"][0]["public_url"]
            print(f"[NGROK] URL pública detectada: {base_url}")
        except Exception:
            base_url = "http://localhost:8000"
            print("[NGROK] ngrok não encontrado, usando localhost")

        for key, games in game_map.items():
            for game in games:
                if "url" in game:
                    game["url"] = base_url + game["url"]

        return game_map

    def find_related_game(self, entities, top_blocks, language):
        found = {}

        # 1. Prioridade: topic_map construído da KB
        for block in top_blocks:
            topic = block["topic"].lower().strip()
            if topic in self.topic_map:
                for game in self.topic_map[topic]:
                    found[game["url"]] = game

        # 2. Fallback: game_map direto por entidades
        if not found:
            candidates = [re.sub(r'[^\w\s]', '', e).lower().strip() for e in entities]
            candidates = [c for c in candidates if c and len(c) > 2]
            for candidate in candidates:
                for key, games in self.game_map.items():
                    if key in candidate or candidate in key:
                        for game in games:
                            found[game["url"]] = game

        return list(found.values())
        
    def build_topic_map(self):
        topic_map = {}
        all_blocks = self.all_blocks_pt + self.all_blocks_en

        # inverte o FRANCHISE_HINTS para lookup rápido: "roxas" -> "kingdom hearts(odeio python)"
        character_to_franchise = {}
        for franchise, characters in FRANCHISE_HINTS.items():
            for char in characters:
                character_to_franchise[char] = franchise

        for block in all_blocks:
            topic = block["topic"].lower().strip()
            if topic in topic_map:
                continue

            # 1. string match direto
            for key, games in self.game_map.items():
                if key in topic or topic in key:
                    topic_map[topic] = games
                    print(f"[TOPIC MAP] '{topic}' → '{key}' (string match)")
                    break

            if topic in topic_map:
                continue

            # 2. lookup por personagem conhecido
            if topic in character_to_franchise:
                franchise = character_to_franchise[topic]
                if franchise in self.game_map:
                    topic_map[topic] = self.game_map[franchise]
                    print(f"[TOPIC MAP] '{topic}' → '{franchise}' (franchise hint)")

        print(f"[TOPIC MAP] {len(topic_map)} topics mapeados")
        return topic_map
