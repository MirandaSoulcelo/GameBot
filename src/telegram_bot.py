from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
import asyncio
from nlp_engine import NLPEngine
import whisper
import os
from telegram import Update
from dotenv import load_dotenv
import requests
import re
import sqlite3
from sentiment import analyze_sentiment
import math
from dictConfig import GAME_DISPLAY_NAMES, FEEDBACK_KEYWORDS


load_dotenv()


def looks_like_feedback(text, language):

    text = text.lower()

    keywords = set(FEEDBACK_KEYWORDS.get(language, []))
    other = "en" if language == "pt" else "pt"
    keywords |= set(FEEDBACK_KEYWORDS.get(other, []))

    return any(word in text for word in keywords)


def injetar_uid(resposta, user_id):
    def substituir(match):
        url = match.group(1)
        if "uid=" in url:
            url = re.sub(r"uid=[^&\s]*", f"uid={user_id}", url)
        else:
            separador = "&" if "?" in url else "?"
            url = f"{url}{separador}uid={user_id}"
        return url
    return re.sub(r"(https?://[^\s]+/play/[^\s]+)", substituir, resposta)

model = whisper.load_model("medium") 
print("Iniciando NLP...")

bot_nlp = NLPEngine()

TOKEN = os.getenv("TELEGRAM_TOKEN")
GIPHY_KEY = os.getenv("GIPHY_KEY")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Fala! \nManda uma pergunta sobre jogos que eu tento te responder :)"
    )
    await update.message.reply_text(
        " Consulte os 5 jogos mais bem avaliados pela comunidade com /ranking"
    )


def buscar_gif_inteligente(topic, entities):
    gif = buscar_gif(topic)
    if gif:
        return gif
    
    for entity in entities:
        palavras_ruido = {"personagem", "character", "the", "of", "de", "o", "a"}
        entity_limpa = " ".join(
            w for w in entity.split() if w not in palavras_ruido
        ).strip()
        if len(entity_limpa) > 2:
            gif = buscar_gif(entity_limpa)
            if gif:
                return gif
    
    return None

async def handle_ranking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ranking = get_ranking()

    if not ranking:
        await update.message.reply_text(
            " Ainda não há avaliações suficientes para gerar um ranking!"
        )
        return
    
    top_game = GAME_DISPLAY_NAMES.get(ranking[0][0], ranking[0][0])
    gif_url = buscar_gif(top_game)
    if gif_url:
        try:
            await update.message.reply_animation(gif_url)
        except Exception as e:
            print(f"[GIF ERROR] {e}")

    lines = []
    for i, row in enumerate(ranking):
        game = row[0]
        display_name = GAME_DISPLAY_NAMES.get(game, game)
        if i == 0:
            lines.append(f"{i + 1}. *{display_name}* ⭐")
        else:
            lines.append(f"{i + 1}. {display_name}")

    await update.message.reply_text(
        "🏆 Top jogos mais bem avaliados pela comunidade:\n\n" + "\n\n".join(lines),
        parse_mode="Markdown"
        )


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.voice.get_file()
    file_path = f"audio_{update.message.message_id}.ogg"
    await file.download_to_drive(file_path)
    await update.message.reply_text("🎧 Processando áudio...")

    texto = await asyncio.to_thread(transcribe_audio, file_path)
    user_id = update.message.from_user.id
    language = bot_nlp.detect_language(texto, "pt")
    recent_session = get_recent_game_session(user_id)

    if recent_session:
        session_id, game_name = recent_session

        if looks_like_feedback(texto, language):
            sentiment = analyze_sentiment(texto)
            save_feedback(user_id, game_name, texto, sentiment["label"], sentiment["score"])
            mark_feedback_asked(session_id)

            sentiment_text = {
                "pt": {"positive": "positiva", "negative": "negativa", "neutral": "neutra"},
                "en": {"positive": "positive", "negative": "negative", "neutral": "neutral"}
            }
            lang_map = sentiment_text.get(language, sentiment_text["en"])

            await update.message.reply_text(
                f" {'Entendi' if language == 'pt' else 'Got it'}! "
                f"{'Parece que você teve uma experiência' if language == 'pt' else 'Seems like you had a'} "
                f"{lang_map[sentiment['label']]} "
                f"{'com' if language == 'pt' else 'experience with'} {game_name} "
            )

            if os.path.exists(file_path):
                os.remove(file_path)
            return  # <-- limpa o arquivo e sai antes do NLP

        else:
            if language == "pt":
                await update.message.reply_text(
                    f" Aliás, vi que você testou {game_name} recentemente.\n"
                    f"Se quiser, me conta depois o que achou "
                )
            else:
                await update.message.reply_text(
                    f" By the way, I saw you tried {game_name} recently.\n"
                    f"If you want, tell me later what you thought about it "
                )

    print(f"Transcrição: {texto}")

    resposta, topic, entities = await asyncio.to_thread(bot_nlp.answer, texto, 0.2, 3, "pt")
    resposta = injetar_uid(resposta, user_id)

    gif_url = buscar_gif_inteligente(topic, entities)
    if gif_url:
        try:
            await update.message.reply_animation(gif_url)
        except Exception as e:
            print(f"[GIF ERROR] {e}")

    await update.message.reply_text(f" Você disse: {texto}\n\n{resposta}")

    if os.path.exists(file_path):
        os.remove(file_path)

def buscar_gif(topic):
    try:
        url = f"https://api.giphy.com/v1/gifs/search?q={topic}&api_key={GIPHY_KEY}&limit=1&rating=g"
        r = requests.get(url).json()
        return r["data"][0]["images"]["original"]["url"]
    except Exception:
        return None

def get_recent_game_session(user_id):

    conn = sqlite3.connect("saves.db")

    row = conn.execute(
        """
        SELECT id, game
        FROM game_sessions
        WHERE user_id = ?
        AND feedback_asked = 0
        ORDER BY opened_at DESC
        LIMIT 1
        """,
        (str(user_id),)
    ).fetchone()

    conn.close()

    return row


def mark_feedback_asked(session_id):

    conn = sqlite3.connect("saves.db")

    conn.execute(
        """
        UPDATE game_sessions
        SET feedback_asked = 1
        WHERE id = ?
        """,
        (session_id,)
    )

    conn.commit()
    conn.close()


def save_feedback(user_id, game, message, sentiment, confidence):

    conn = sqlite3.connect("saves.db")

    conn.execute(
        """
        INSERT INTO game_feedback
        (user_id, game, message, sentiment, confidence)
        VALUES (?, ?, ?, ?, ?)
        """,
        (str(user_id), game, message, sentiment, confidence)
    )

    conn.commit()
    conn.close()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_id = update.message.from_user.id
    language = bot_nlp.detect_language(user_text, "pt")
    recent_session = get_recent_game_session(user_id)

    print(f"[DEBUG FEEDBACK] recent_session={recent_session}")
    print(f"[DEBUG FEEDBACK] looks_like_feedback={looks_like_feedback(user_text, language)}")
    print(f"[DEBUG FEEDBACK] language={language}")

    if recent_session:
        session_id, game_name = recent_session

        if looks_like_feedback(user_text, language):
            sentiment = analyze_sentiment(user_text)
            save_feedback(user_id, game_name, user_text, sentiment["label"], sentiment["score"])
            mark_feedback_asked(session_id)

            sentiment_text = {
                "pt": {"positive": "positiva", "negative": "negativa", "neutral": "neutra"},
                "en": {"positive": "positive", "negative": "negative", "neutral": "neutral"}
            }
            lang_map = sentiment_text.get(language, sentiment_text["en"])

            await update.message.reply_text(
                f" {'Entendi' if language == 'pt' else 'Got it'}! "
                f"{'Parece que você teve uma experiência' if language == 'pt' else 'Seems like you had a'} "
                f"{lang_map[sentiment['label']]} "
                f"{'com' if language == 'pt' else 'experience with'} {game_name} "
            )
            return

        else:
            if language == "pt":
                await update.message.reply_text(
                    f" Aliás 👀 vi que você testou {game_name} recentemente.\n"
                    f"Se quiser, me conta depois o que achou"
                )
            else:
                await update.message.reply_text(
                    f" By the way 👀 I saw you tried {game_name} recently.\n"
                    f"If you want, tell me later what you thought about it "
                )

    resposta, topic, entities = await asyncio.to_thread(bot_nlp.answer, user_text, 0.2, 3, "pt")
    resposta = injetar_uid(resposta, user_id)

    gif_url = buscar_gif_inteligente(topic, entities)
    if gif_url:
        try:
            await update.message.reply_animation(gif_url)
        except Exception as e:
            print(f"[GIF ERROR] {e}")

    await update.message.reply_text(resposta)

def get_game_url(game_slug):
    for key, games in bot_nlp.game_map.items():
        for g in games:
            if g["url"].endswith(f"/play/{game_slug}"):
                return g["url"]
    return ""

def get_ranking():
    conn = sqlite3.connect("saves.db")
    rows = conn.execute(
        """
        SELECT 
            game,
            SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) as positivos,
            SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) as negativos,
            COUNT(*) as total
        FROM game_feedback
        GROUP BY game
        HAVING total >= 2
        """
    ).fetchall()
    conn.close()

    def score(row):
        _, positivos, negativos, total = row
        negativos_ponderados = negativos * 1.5
        denominador = positivos + negativos_ponderados
        if denominador == 0:
            return 0
        proporcao = positivos / denominador
        return proporcao * math.log(total + 1)

    ranking = sorted(rows, key=score, reverse=True)[:5]
    return ranking

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.VOICE, handle_voice))
app.add_handler(CommandHandler("ranking", handle_ranking))

print("Bot rodando")
app.run_polling()