import re
from nltk.corpus import stopwords
import nltk

nltk.download('stopwords', quiet=True)

STOPWORDS_PT = set(stopwords.words("portuguese"))
STOPWORDS_EN = set(stopwords.words("english"))

SECTION_TO_INTENT = {
    # inglês
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
    "aparições":      "crossovers",
    "outras mídias":  "crossovers",
    "lançamentos":    "jogos",
    "títulos":        "jogos",
    "jogos":          "jogos",
    "desenvolvimento": "curiosidades",
    "recepção":       "curiosidades",
    "curiosidades":   "curiosidades",
    "mundo":          "mundo_universo",
    "universo":       "mundo_universo",
    "locais":         "mundo_universo",
    "empresa":        "empresas",
    "franquia":       "franquias",
    "série":          "franquias",
}


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