import nltk
import requests
from bs4 import BeautifulSoup

nltk.download('punkt',     quiet=True)
nltk.download('punkt_tab', quiet=True)


SECTION_TO_INTENT = {
    "gameplay":       "gameplay",
    "mechanics":      "gameplay",
    "controls":       "gameplay",
    "story":          "historia_lore",
    "plot":           "historia_lore",
    "history":        "historia_lore",
    "background":     "historia_lore",
    "narrative":      "historia_lore",
    "abilities":      "habilidades",
    "powers":         "habilidades",
    "moves":          "habilidades",
    "skills":         "habilidades",
    "techniques":     "habilidades",
    "personality":    "personagens",
    "biography":      "personagens",
    "character":      "personagens",
    "design":         "personagens",
    "appearances":    "crossovers",
    "in other games": "crossovers",
    "other media":    "crossovers",
    "games":          "jogos",
    "releases":       "jogos",
    "titles":         "jogos",
    "discography":    "jogos",
    "development":    "curiosidades",
    "reception":      "curiosidades",
    "overview":       "curiosidades",
    "trivia":         "curiosidades",
    "world":          "mundo_universo",
    "setting":        "mundo_universo",
    "universe":       "mundo_universo",
    "locations":      "mundo_universo",
    "company":        "empresas",
    "organization":   "empresas",
    "franchise":      "franquias",
    "series":         "franquias",
    # português
    "jogabilidade":   "gameplay",
    "mecânicas":      "gameplay",
    "controles":      "gameplay",
    "história":       "historia_lore",
    "enredo":         "historia_lore",
    "trama":          "historia_lore",
    "habilidades":    "habilidades",
    "poderes":        "habilidades",
    "golpes":         "habilidades",
    "técnicas":       "habilidades",
    "personalidade":  "personagens",
    "biografia":      "personagens",
    "design":         "personagens",
    "aparições":      "crossovers",
    "outras mídias":  "crossovers",
    "lançamentos":    "jogos",
    "títulos":        "jogos",
    "jogos":          "jogos",
    "desenvolvimento":"curiosidades",
    "recepção":       "curiosidades",
    "curiosidades":   "curiosidades",
    "mundo":          "mundo_universo",
    "universo":       "mundo_universo",
    "locais":         "mundo_universo",
    "empresa":        "empresas",
    "franquia":       "franquias",
    "série":          "franquias",
}


def heading_to_intent(heading_text):
    h = heading_text.lower().strip()
    for key, intent in SECTION_TO_INTENT.items():
        if key in h:
            return intent
    return None


def clean_sentence(sentence):
    import re
    sentence = re.sub(r'\[\d+\]', '', sentence)
    sentence = re.sub(r'\{\{[^}]+\}\}', '', sentence)
    sentence = sentence.replace('\n', ' ').strip()
    sentence = re.sub(r'\s+', ' ', sentence)
    return sentence


def is_valid_sentence(sentence):
    words = sentence.split()
    if len(words) < 4:
        return False
    if sentence.startswith('[') or sentence.startswith('('):
        return False
    if sentence.count(',') > 8:
        return False
    return True


def scrape_page(url, topic, language="english"):

    blocks = []
    current_intent = "curiosidades"

    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)

        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup.find_all(["script", "style"]):
            tag.decompose()

        content = (
            soup.select_one("#mw-content-text")  or
            soup.select_one(".mw-parser-output") or
            soup.select_one("#bodyContent")      or
            soup
        )

        paragraphs = content.find_all("p")
        print(f"  [DEBUG] Parágrafos encontrados: {len(paragraphs)}")

        if not paragraphs:
            print(f"  [AVISO] Nenhum parágrafo encontrado em: {url}")
            return blocks

        for tag in content.find_all(["h2", "h3", "p"]):

            if tag.name in ["h2", "h3"]:
                heading_text = tag.get_text()
                detected = heading_to_intent(heading_text)
                if detected:
                    current_intent = detected

            elif tag.name == "p":
                raw = tag.get_text().strip()
                if not raw:
                    continue

                sentences = nltk.sent_tokenize(raw, language=language)

                for i in range(0, len(sentences), 2):
                    block_text = " ".join(sentences[i:i+2])
                    block_text = clean_sentence(block_text)

                    if not is_valid_sentence(block_text):
                        continue

                    blocks.append({
                        "topic":  topic,
                        "source": url,
                        "intent": current_intent,
                        "text":   block_text
                    })

    except Exception as e:
        print(f"  [ERRO] {url}: {e}")

    return blocks


def collect_articles(urls_with_topics, language="english"):

    all_blocks = []

    for url, topic in urls_with_topics:
        print(f"Coletando: [{topic}] {url}")
        blocks = scrape_page(url, topic, language)
        print(f"  → {len(blocks)} blocos")
        all_blocks.extend(blocks)

    print(f"\nTotal coletado: {len(all_blocks)} blocos\n")
    return all_blocks