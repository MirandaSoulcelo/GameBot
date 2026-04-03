# 🎮 GameBot — Chatbot Inteligente sobre Jogos

> Bot do Telegram com NLP, reconhecimento de voz e base de conhecimento construída com web scraping — tudo focado no universo gamer.

---

## ✨ O que esse projeto faz

O **GameBot** é um chatbot para Telegram capaz de responder perguntas sobre personagens, franquias, empresas, gameplay, história e muito mais do mundo dos games. Ele suporta tanto **texto** quanto **mensagens de voz**, e funciona em **português e inglês**.

### Funcionalidades principais

* 🧠 **Motor NLP próprio** — combina TF-IDF + similaridade vetorial (spaCy) para encontrar as respostas mais relevantes
* 🎙️ **Reconhecimento de voz** — transcreve áudios enviados no Telegram usando Whisper (OpenAI)
* 🌐 **Base de conhecimento dinâmica** — construída via web scraping de wikis especializadas
* 🗣️ **Bilíngue** — detecta automaticamente se a pergunta é em PT ou EN
* 🎯 **Detecção de intenção** — classifica perguntas em categorias
* 🔍 **Pré-processamento avançado** — lematização, stopwords e NER

---

## 🗂️ Estrutura do projeto

```bash
├── bot.py
├── nlp_engine.py
├── knowledge_base_builder.py
├── web_scraper.py
├── knowledge_base_en.json
├── knowledge_base_pt.json
└── .env
```

---

## ⚙️ Como rodar

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/gamebot.git
cd gamebot
```

### 2. Crie e ative um ambiente virtual

```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Baixe os modelos do spaCy

```bash
python -m spacy download en_core_web_lg
python -m spacy download pt_core_news_lg
```

### 5. Configure o token do Telegram

Crie um `.env`:

```env
TELEGRAM_TOKEN=seu_token_aqui
```

### 6. Gere a base de conhecimento

```bash
python knowledge_base_builder.py
```

### 7. Inicie o bot

```bash
python bot.py
```

---

## 💬 Como usar

* Envie uma pergunta em texto
* Ou mande um áudio 🎙️
* Funciona em PT 🇧🇷 e EN 🇺🇸

**Exemplos:**

* Quem é o Bowser?
* What are Sonic's abilities?
* Qual a história de Kingdom Hearts?
* Quem criou a Nintendo?

---

## 🧩 Categorias suportadas

| Categoria      | Exemplos           |
| -------------- | ------------------ |
| 👤 Personagens | Mario, Link, Sonic |
| 🏢 Empresas    | Nintendo, Sega     |
| 📦 Franquias   | Zelda, Pokémon     |
| 🎮 Gameplay    | Mecânicas          |
| 📖 História    | Lore               |
| ⚡ Habilidades  | Poderes            |
| 🌍 Mundos      | Hyrule             |
| 🔀 Crossovers  | Aparições          |

---

## 📸 Screenshots

*(em breve)*

---

## 📄 Licença

MIT
