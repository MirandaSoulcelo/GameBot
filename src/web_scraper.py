import nltk
import requests
from bs4 import BeautifulSoup
from text_processing import heading_to_intent, clean_sentence, is_valid_sentence

nltk.download('punkt',     quiet=True)
nltk.download('punkt_tab', quiet=True)

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
        print(f"  Parágrafos encontrados: {len(paragraphs)}")

        if not paragraphs:
            print(f"   Nenhum parágrafo encontrado em: {url}")
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