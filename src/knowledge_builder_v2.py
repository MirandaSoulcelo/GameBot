from web_scraper import collect_articles
from langdetect import detect, DetectorFactory
from nltk.corpus import stopwords
import nltk
import json
import re

nltk.download('stopwords', quiet=True)
DetectorFactory.seed = 0

STOPWORDS_PT = set(stopwords.words("portuguese"))
STOPWORDS_EN = set(stopwords.words("english"))


def clean_sentence(sentence):
    sentence = re.sub(r'\[\d+\]', '', sentence)
    sentence = re.sub(r'\{\{[^}]+\}\}', '', sentence)
    sentence = sentence.replace('\n', ' ').strip()
    sentence = re.sub(r'\s+', ' ', sentence)
    return sentence


def is_valid_sentence(sentence):
    if len(sentence.split()) < 6:
        return False
    if sentence.startswith('[') or sentence.startswith('('):
        return False
    if sentence.count(',') > 6:
        return False
    return True


def remove_stopwords(sentence, language="pt"):
    """
    Remove stop words usando NLTK — requisito explícito da disciplina.
    Retorna a frase limpa (usada no pré-processamento da KB).
    """
    sw = STOPWORDS_PT if language == "pt" else STOPWORDS_EN
    words = sentence.lower().split()
    filtered = [w for w in words if w not in sw]
    return " ".join(filtered)



def empty_kb():
    """
    A KB agora armazena blocos (dicionários) em vez de frases soltas.
    Cada bloco carrega: topic, source, intent e text.
    Isso resolve o problema de 'frases sem contexto'.
    """
    return {
        "personagens":    [],
        "franquias":      [],
        "jogos":          [],
        "empresas":       [],
        "gameplay":       [],
        "historia_lore":  [],
        "habilidades":    [],
        "mundo_universo": [],
        "crossovers":     [],
        "curiosidades":   []
    }


SECTION_TO_INTENT = {
    # inglês
    "gameplay":      "gameplay",
    "story":         "historia_lore",
    "plot":          "historia_lore",
    "history":       "historia_lore",
    "abilities":     "habilidades",
    "powers":        "habilidades",
    "moves":         "habilidades",
    "personality":   "personagens",
    "biography":     "personagens",
    "appearances":   "crossovers",
    "in other games":"crossovers",
    "games":         "jogos",
    "releases":      "jogos",
    "development":   "curiosidades",
    "reception":     "curiosidades",
    "overview":      "curiosidades",
    "world":         "mundo_universo",
    "setting":       "mundo_universo",
    "universe":      "mundo_universo",
    "company":       "empresas",
    "franchise":     "franquias",
    "series":        "franquias",
    # português
    "jogabilidade":  "gameplay",
    "história":      "historia_lore",
    "enredo":        "historia_lore",
    "habilidades":   "habilidades",
    "poderes":       "habilidades",
    "aparições":     "crossovers",
    "personalidade": "personagens",
    "biografia":     "personagens",
    "lançamentos":   "jogos",
    "mundo":         "mundo_universo",
    "universo":      "mundo_universo",
    "empresa":       "empresas",
    "franquia":      "franquias",
    "série":         "franquias",
}


def heading_to_intent(heading_text):
    """
    Converte o texto de um heading (h2/h3) em uma intenção.
    Muito mais confiável que matching de substrings em frases.
    """
    h = heading_text.lower().strip()
    for key, intent in SECTION_TO_INTENT.items():
        if key in h:
            return intent
    return None  


def classify_sentence_fallback(sentence):
    """
    Classificador de fallback por substring — usado apenas quando
    a página não tem headings claros (ex: Wikipedia genérica).
    """
    s = sentence.lower()

    if any(x in s for x in [
        "character", "antagonist", "is the protagonist", "main character",
        "protagonist", "playable character", "mascot",
        "é um personagem", "é a protagonista", "personagem fictício",
        "personagem jogável", "mascote da"
    ]):
        return "personagens"

    if any(x in s for x in [
        "developed by", "published by", "video game company",
        "game developer", "game publisher",
        "desenvolvido por", "publicado por",
        "empresa de jogos", "desenvolvedora", "publicadora"
    ]):
        return "empresas"

    if any(x in s for x in [
        "is a video game franchise", "is a media franchise",
        "is a game series", "franchise created by",
        "é uma franquia", "é uma série de jogos", "série criada por"
    ]):
        return "franquias"

    if any(x in s for x in [
        "video game released", "released in", "launch title",
        "installment", "lançado em", "foi lançado",
        "título da série", "jogo da série"
    ]):
        return "jogos"

    if any(x in s for x in [
        "the player controls", "players control", "gameplay",
        "game mechanics", "features combat", "the game features",
        "permite ao jogador", "o jogador controla", "jogabilidade",
        "mecânicas de jogo"
    ]):
        return "gameplay"

    if any(x in s for x in [
        "the story follows", "the plot", "must rescue",
        "takes place in", "the narrative",
        "a história segue", "o enredo", "deve salvar",
        "se passa em", "a narrativa"
    ]):
        return "historia_lore"

    if any(x in s for x in [
        "can use", "has the ability", "special ability",
        "can attack", "powers include",
        "habilidade", "poder", "ataque", "pode usar"
    ]):
        return "habilidades"

    if any(x in s for x in [
        "fictional world", "kingdom", "universe",
        "setting of the series",
        "mundo fictício", "reino", "universo", "ambientado em"
    ]):
        return "mundo_universo"

    if any(x in s for x in [
        "appears in", "crossover", "guest character",
        "playable in", "aparece em", "personagem convidado"
    ]):
        return "crossovers"

    return "curiosidades"

def build_knowledge_base():

    urls_en = [
        ("https://www.mariowiki.com/Mario",                               "Mario"),
        ("https://www.mariowiki.com/Luigi",                               "Luigi"),
        ("https://www.mariowiki.com/Princess_Peach",                      "Princess Peach"),
        ("https://www.mariowiki.com/Bowser",                              "Bowser"),
        ("https://zeldawiki.gg/wiki/Link",                                "Link"),
        ("https://zeldawiki.gg/wiki/Zelda",                               "Princess Zelda"),
        ("https://zeldawiki.gg/wiki/Ganondorf",                           "Ganondorf"),
        ("https://en.wikipedia.org/wiki/Sonic_the_Hedgehog_(character)",             "Sonic"),
        ("https://en.wikipedia.org/wiki/Tails_(Sonic_the_Hedgehog)",     "Tails"),
        ("https://en.wikipedia.org/wiki/Sora_(Kingdom_Hearts)",          "Sora"),
        ("https://bulbapedia.bulbagarden.net/wiki/Pikachu_(Pok%C3%A9mon)","Pikachu"),
        ("https://bulbapedia.bulbagarden.net/wiki/Charizard_(Pok%C3%A9mon)","Charizard"),
        ("https://bulbapedia.bulbagarden.net/wiki/Mewtwo_(Pok%C3%A9mon)", "Mewtwo"),
        ("https://www.mariowiki.com/Donkey_Kong",                         "Donkey Kong"),
        # franquias
        ("https://en.wikipedia.org/wiki/Super_Mario",                     "Super Mario Franchise"),
        ("https://en.wikipedia.org/wiki/The_Legend_of_Zelda",            "Zelda Franchise"),
        ("https://en.wikipedia.org/wiki/Pok%C3%A9mon",                   "Pokémon Franchise"),
        ("https://en.wikipedia.org/wiki/Sonic_the_Hedgehog",             "Sonic Franchise"),
        ("https://en.wikipedia.org/wiki/Kingdom_Hearts",                  "Kingdom Hearts Franchise"),
        ("https://en.wikipedia.org/wiki/Donkey_Kong",                     "Donkey Kong Franchise"),
        # empresas
        ("https://en.wikipedia.org/wiki/Nintendo",                        "Nintendo"),
        ("https://en.wikipedia.org/wiki/Sega",                            "Sega"),
        ("https://en.wikipedia.org/wiki/Capcom",                          "Capcom"),
        # mundos/universos
        ("https://zeldawiki.gg/wiki/Hyrule",                              "Hyrule"),
        ("https://bulbapedia.bulbagarden.net/wiki/Kanto",                 "Kanto Region"),
    ]

    urls_pt = [
        # personagens principais
        ("https://pt.wikipedia.org/wiki/Mario",                           "Mario"),
        ("https://pt.wikipedia.org/wiki/Link_(The_Legend_of_Zelda)",      "Link"),
        ("https://pt.wikipedia.org/wiki/Sonic_the_Hedgehog_(personagem)", "Sonic"),
        ("https://pt.wikipedia.org/wiki/Pikachu",                         "Pikachu"),
        ("https://pt.wikipedia.org/wiki/Sora_(Kingdom_Hearts)",           "Sora"),
        ("https://pt.wikipedia.org/wiki/Donkey_Kong",                     "Donkey Kong"),
        # franquias
        ("https://pt.wikipedia.org/wiki/Super_Mario",                     "Super Mario"),
        ("https://pt.wikipedia.org/wiki/The_Legend_of_Zelda",            "Zelda"),
        ("https://pt.wikipedia.org/wiki/Pok%C3%A9mon",                   "Pokémon"),
        ("https://pt.wikipedia.org/wiki/Sonic_the_Hedgehog",             "Sonic"),
        ("https://pt.wikipedia.org/wiki/Kingdom_Hearts",                  "Kingdom Hearts"),
        # empresas
        ("https://pt.wikipedia.org/wiki/Nintendo",                        "Nintendo"),
        ("https://pt.wikipedia.org/wiki/Sega",                            "Sega"),
        ("https://pt.wikipedia.org/wiki/Capcom",                          "Capcom"),
        # mundos
        ("https://pt.wikipedia.org/wiki/Kanto_(Pok%C3%A9mon)",           "Kanto"),
    ]

    kb_en = empty_kb()
    kb_pt = empty_kb()

    LANGS_ROMANICAS = {"pt", "es", "it", "fr", "ro"}

    print("=" * 50)
    print("Scrapeando inglês...")
    print("=" * 50)
    blocks_en = collect_articles(urls_en, language="english")

    for block in blocks_en:
        text = block["text"]
        topic = block["topic"]
        source = block["source"]

        intent = block.get("intent") or classify_sentence_fallback(text)

        text_clean = clean_sentence(text)
        if not is_valid_sentence(text_clean):
            continue

        try:
            if detect(text_clean) == "en":
                text_sem_sw = remove_stopwords(text_clean, language="en")

                kb_en[intent].append({
                    "topic":  topic,
                    "source": source,
                    "intent": intent,
                    "text":   text_clean,  
                    "text_clean": text_sem_sw  
                })
        except Exception:
            continue

    print("=" * 50)
    print("Scrapeando português...")
    print("=" * 50)
    blocks_pt = collect_articles(urls_pt, language="portuguese")

    for block in blocks_pt:
        text = block["text"]
        topic = block["topic"]
        source = block["source"]

        intent = block.get("intent") or classify_sentence_fallback(text)

        text_clean = clean_sentence(text)
        if not is_valid_sentence(text_clean):
            continue

        try:
            if detect(text_clean) in LANGS_ROMANICAS:
                text_sem_sw = remove_stopwords(text_clean, language="pt")

                kb_pt[intent].append({
                    "topic":  topic,
                    "source": source,
                    "intent": intent,
                    "text":   text_clean,
                    "text_clean": text_sem_sw
                })
        except Exception:
            continue

    with open("knowledge_base_en.json", "w", encoding="utf-8") as f:
        json.dump(kb_en, f, indent=4, ensure_ascii=False)

    with open("knowledge_base_pt.json", "w", encoding="utf-8") as f:
        json.dump(kb_pt, f, indent=4, ensure_ascii=False)

    print("\n" + "=" * 50)
    print("KB gamer criada com sucesso!")
    print("=" * 50)
    for lang, kb in [("EN", kb_en), ("PT", kb_pt)]:
        total = sum(len(v) for v in kb.values())
        print(f"\n[{lang}] Total de blocos: {total}")
        for intent, blocks in kb.items():
            if blocks:
                print(f"  {intent}: {len(blocks)} blocos")


if __name__ == "__main__":
    build_knowledge_base()