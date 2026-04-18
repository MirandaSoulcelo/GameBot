from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import asyncio
from nlp_engine import NLPEngine
import whisper
import os
from telegram import Update
from dotenv import load_dotenv
import requests


load_dotenv()

model = whisper.load_model("medium") 
print("Iniciando NLP...")

bot_nlp = NLPEngine()

TOKEN = os.getenv("TELEGRAM_TOKEN")
GIPHY_KEY = os.getenv("GIPHY_KEY")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Fala! \nManda uma pergunta sobre jogos que eu tento te responder :) ")

def transcribe_audio(file_path):
    result = model.transcribe(file_path)
    return result["text"]


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.voice.get_file()

    file_path = f"audio_{update.message.message_id}.ogg"
    await file.download_to_drive(file_path)

    await update.message.reply_text("🎧 Processando áudio...")

    texto = await asyncio.to_thread(transcribe_audio, file_path)

    print(f"Transcrição: {texto}")

    resposta, topic = await asyncio.to_thread(bot_nlp.answer, texto, 0.2, 3, "pt")
    gif_url = buscar_gif(topic)
    if gif_url:
        await update.message.reply_animation(gif_url)
    await update.message.reply_text(f"🧠 Você disse: {texto}\n\n{resposta}")

   
    if os.path.exists(file_path):
        os.remove(file_path)

def buscar_gif(topic):
    try:
        url = f"https://api.giphy.com/v1/gifs/search?q={topic}&api_key={GIPHY_KEY}&limit=1&rating=g"
        r = requests.get(url).json()
        return r["data"][0]["images"]["original"]["url"]
    except Exception:
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    print(f"Usuário: {user_text}")

    resposta, topic = await asyncio.to_thread(bot_nlp.answer, user_text, 0.2, 3, "pt")

    print(f"Bot: {resposta}")

    gif_url = buscar_gif(topic)
    if gif_url:
        await update.message.reply_animation(gif_url)

    await update.message.reply_text(resposta)

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(MessageHandler(filters.COMMAND, start))
app.add_handler(MessageHandler(filters.VOICE, handle_voice))

print("Bot rodando")
app.run_polling()