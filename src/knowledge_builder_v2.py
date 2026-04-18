from web_scraper import collect_articles
from text_processing import clean_sentence, is_valid_sentence, remove_stopwords, classify_sentence_fallback
from langdetect import detect, DetectorFactory
import nltk
import json

nltk.download('stopwords', quiet=True)
DetectorFactory.seed = 0


def empty_kb():
    
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


def build_knowledge_base():

    urls_en = [
        ("https://www.mariowiki.com/Mario",                                "Mario"),
        ("https://www.mariowiki.com/Luigi",                                "Luigi"),
        ("https://www.mariowiki.com/Princess_Peach",                       "Princess Peach"),
        ("https://www.mariowiki.com/Bowser",                               "Bowser"),
        ("https://en.wikipedia.org/wiki/Link_(personagem)",       "Link"),
        ("https://en.wikipedia.org/wiki/Princess_Zelda",                   "Princess Zelda"),
        ("https://en.wikipedia.org/wiki/Ganondorf",                        "Ganondorf"),
        ("https://en.wikipedia.org/wiki/Hyrule",                           "Hyrule"),
        ("https://en.wikipedia.org/wiki/Sonic_the_Hedgehog_(character)",   "Sonic"),
        ("https://en.wikipedia.org/wiki/Tails_(Sonic_the_Hedgehog)",       "Tails"),
        ("https://en.wikipedia.org/wiki/Sora_(Kingdom_Hearts)",            "Sora"),
        ("https://bulbapedia.bulbagarden.net/wiki/Pikachu_(Pok%C3%A9mon)", "Pikachu"),
        ("https://bulbapedia.bulbagarden.net/wiki/Charizard_(Pok%C3%A9mon)", "Charizard"),
        ("https://bulbapedia.bulbagarden.net/wiki/Mewtwo_(Pok%C3%A9mon)",  "Mewtwo"),
        ("https://www.mariowiki.com/Donkey_Kong",                          "Donkey Kong"),
        ("https://en.wikipedia.org/wiki/Ventus_(Kingdom_Hearts)",          "Ventus"),
        ("https://en.wikipedia.org/wiki/Aqua_(Kingdom_Hearts)",            "Aqua"),
        ("https://en.wikipedia.org/wiki/Riku_(Kingdom_Hearts)",            "Riku"),
        ("https://en.wikipedia.org/wiki/Xion_(Kingdom_Hearts)",            "Xion"),
        ("https://en.wikipedia.org/wiki/Namin%C3%A9",                      "Namine"),
        ("https://en.wikipedia.org/wiki/Vanitas_(Kingdom_Hearts)",         "Vanitas"),
        ("https://en.wikipedia.org/wiki/Roxas_(Kingdom_Hearts)",         "Roxas"),
        ("https://en.wikipedia.org/wiki/Shadow_the_Hedgehog)",         "Shadow"),
        ("https://en.wikipedia.org/wiki/Lista_de_personagens_de_Sonic_the_Hedgehog",         "Knuckles"),
        ("https://en.wikipedia.org/wiki/Lista_de_personagens_de_Sonic_the_Hedgehog",         "Eggman"),
        ("https://en.wikipedia.org/wiki/Tails",         "Tails"),
        ("https://wikirby.com/wiki/Kirby",                                 "Kirby"),
        ("https://en.wikipedia.org/wiki/Kirby_(character)",                "Kirby"),
        ("https://en.wikipedia.org/wiki/Star_Fox_(character)",             "Star Fox"),
        ("https://en.wikipedia.org/wiki/Fox_McCloud",                      "Fox McCloud"),
        ("https://en.wikipedia.org/wiki/Super_Smash_Bros.",                      "Super smash bros"),
        ("https://en.wikipedia.org/wiki/Chrono_Trigger",                      "Chrono Trigger"),
        # franquias
        ("https://en.wikipedia.org/wiki/Super_Mario",                      "Super Mario Franchise"),
        ("https://en.wikipedia.org/wiki/The_Legend_of_Zelda",             "Zelda Franchise"),
        ("https://en.wikipedia.org/wiki/Pok%C3%A9mon",                    "Pokémon Franchise"),
        ("https://en.wikipedia.org/wiki/Sonic_the_Hedgehog",              "Sonic Franchise"),
        ("https://en.wikipedia.org/wiki/Kingdom_Hearts",                   "Kingdom Hearts Franchise"),
        ("https://en.wikipedia.org/wiki/Donkey_Kong",                      "Donkey Kong Franchise"),
        # empresas
        ("https://en.wikipedia.org/wiki/Nintendo",                         "Nintendo"),
        ("https://en.wikipedia.org/wiki/Sega",                             "Sega"),
        ("https://en.wikipedia.org/wiki/Capcom",                           "Capcom"),
        # mundos/universos
        ("https://zeldawiki.gg/wiki/Hyrule",                               "Hyrule"),
        ("https://bulbapedia.bulbagarden.net/wiki/Kanto",                  "Kanto Region"),
    ]

    urls_pt = [
        # personagens principais
        ("https://pt.wikipedia.org/wiki/Mario",                            "Mario"),
        ("https://pt.wikipedia.org/wiki/Link_(The_Legend_of_Zelda)",       "Link"),
        ("https://pt.wikipedia.org/wiki/Sonic_the_Hedgehog_(personagem)",  "Sonic"),
        ("https://pt.wikipedia.org/wiki/Pikachu",                          "Pikachu"),
        ("https://pt.wikipedia.org/wiki/Sora_(Kingdom_Hearts)",            "Sora"),
        ("https://pt.wikipedia.org/wiki/Donkey_Kong",                      "Donkey Kong"),
        ("https://pt.wikipedia.org/wiki/Link_(personagem)",       "Link"),
        ("https://pt.wikipedia.org/wiki/Princesa_Zelda",                   "Princess Zelda"),
        ("https://pt.wikipedia.org/wiki/Ganondorf",                        "Ganondorf"),
        ("https://pt.wikipedia.org/wiki/Hyrule",                           "Hyrule"),
        ("https://pt.wikipedia.org/wiki/Ventus_(Kingdom_Hearts)",          "Ventus"),
        ("https://pt.wikipedia.org/wiki/Aqua_(Kingdom_Hearts)",            "Aqua"),
        ("https://pt.wikipedia.org/wiki/Riku_(Kingdom_Hearts)",            "Riku"),
        ("https://pt.wikipedia.org/wiki/Xion_(Kingdom_Hearts)",            "Xion"),
        ("https://pt.wikipedia.org/wiki/Namin%C3%A9",                      "Namine"),
        ("https://pt.wikipedia.org/wiki/Shadow_the_Hedgehog)",         "Shadow"),
        ("https://en.wikipedia.org/wiki/Lista_de_personagens_de_Sonic_the_Hedgehog",         "Knuckles"),
        ("https://pt.wikipedia.org/wiki/Lista_de_personagens_de_Sonic_the_Hedgehog",         "Eggman"),
        ("https://pt.wikipedia.org/wiki/Tails",         "Tails"),
        ("https://pt.wikipedia.org/wiki/Super_Smash_Bros.",                      "Super smash bros"),
        ("https://pt.wikipedia.org/wiki/Chrono_Trigger",                      "Chrono Trigger"),
        # franquias
        ("https://pt.wikipedia.org/wiki/Super_Mario",                      "Super Mario"),
        ("https://pt.wikipedia.org/wiki/The_Legend_of_Zelda",             "Zelda"),
        ("https://pt.wikipedia.org/wiki/Pok%C3%A9mon",                    "Pokémon"),
        ("https://pt.wikipedia.org/wiki/Sonic_the_Hedgehog",              "Sonic"),
        ("https://pt.wikipedia.org/wiki/Kingdom_Hearts",                   "Kingdom Hearts"),
        # empresas
        ("https://pt.wikipedia.org/wiki/Nintendo",                         "Nintendo"),
        ("https://pt.wikipedia.org/wiki/Sega",                             "Sega"),
        ("https://pt.wikipedia.org/wiki/Capcom",                           "Capcom"),
        # mundos
        ("https://pt.wikipedia.org/wiki/Kanto_(Pok%C3%A9mon)",            "Kanto"),
        # Kirby
        ("https://pt.wikipedia.org/wiki/Kirby_(personagem)",               "Kirby"),
        ("https://pt.wikipedia.org/wiki/Kirby_(s%C3%A9rie)",               "Kirby"),
        # Star Fox
        ("https://pt.wikipedia.org/wiki/Star_Fox_(personagem)",            "Star Fox"),
        ("https://pt.wikipedia.org/wiki/Star_Fox",                         "Star Fox"),
        # KH geral (cobre Riku, Kairi e outros secundários)
        ("https://pt.wikipedia.org/wiki/Kingdom_Hearts",                   "Kingdom Hearts"),
    ]

    kb_en = empty_kb()
    kb_pt = empty_kb()

    LANGS_ROMANICAS = {"pt", "es", "it", "fr", "ro"}

    print("=" * 50)
    print("Scrapeando inglês...")
    print("=" * 50)
    blocks_en = collect_articles(urls_en, language="english")

    for block in blocks_en:
        text   = block["text"]
        topic  = block["topic"]
        source = block["source"]
        intent = block.get("intent") or classify_sentence_fallback(text)

        text_clean = clean_sentence(text)
        if not is_valid_sentence(text_clean):
            continue

        try:
            if detect(text_clean) == "en":
                kb_en[intent].append({
                    "topic":      topic,
                    "source":     source,
                    "intent":     intent,
                    "text":       text_clean,
                    "text_clean": remove_stopwords(text_clean, language="en")
                })
        except Exception:
            continue

    print("=" * 50)
    print("Scrapeando português...")
    print("=" * 50)
    blocks_pt = collect_articles(urls_pt, language="portuguese")

    for block in blocks_pt:
        text   = block["text"]
        topic  = block["topic"]
        source = block["source"]
        intent = block.get("intent") or classify_sentence_fallback(text)

        text_clean = clean_sentence(text)
        if not is_valid_sentence(text_clean):
            continue

        try:
            if detect(text_clean) in LANGS_ROMANICAS:
                kb_pt[intent].append({
                    "topic":      topic,
                    "source":     source,
                    "intent":     intent,
                    "text":       text_clean,
                    "text_clean": remove_stopwords(text_clean, language="pt")
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