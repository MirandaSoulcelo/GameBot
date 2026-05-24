<p align="center">
  <img src="https://github.com/user-attachments/assets/9e971e7b-7144-497d-8f65-e3ae50a677ee" width="500"/>
</p>

# 🎮 GameBot — Chatbot Inteligente sobre Jogos

> Bot do Telegram com NLP, reconhecimento de voz, emulador de jogos no browser e base de conhecimento construída com web scraping — tudo focado no universo da Nintendo e Kingdom Hearts porque o criador desse bot é apaixonado.

---

## ✨ O que esse projeto faz

O **GameBot** é um chatbot para Telegram capaz de responder perguntas sobre personagens, franquias, empresas, gameplay, história e muito mais do mundo dos games da Nintendo. Ele suporta tanto **texto** quanto **mensagens de voz**, funciona em **português e inglês**, e ainda permite que o usuário **jogue os jogos diretamente no browser** através de links enviados pelo bot.

### Funcionalidades principais

* 🧠 **Motor NLP próprio** — combina TF-IDF + similaridade vetorial (spaCy) para encontrar as respostas mais relevantes
* 🎙️ **Reconhecimento de voz** — transcreve áudios enviados no Telegram usando Whisper (OpenAI)
* 🌐 **Base de conhecimento dinâmica** — construída via web scraping de wikis especializadas
* 🗣️ **Bilíngue** — detecta automaticamente se a pergunta é em PT ou EN
* 🎯 **Detecção de intenção** — classifica perguntas em categorias como personagens, gameplay, história, etc.
* 🔍 **Pré-processamento avançado** — lematização, remoção de stopwords e reconhecimento de entidades (NER)
* 🎮 **Emulador no browser** — ao responder sobre um jogo disponível, o bot envia o link para jogar direto no browser via EmulatorJS
* 💾 **Save persistente** — progresso do jogador (`.srm` e save states) salvo em banco SQLite via API FastAPI, independente do cache do browser
* 😄 **Coleta de feedback** — após o usuário jogar, o bot detecta automaticamente avaliações positivas ou negativas na conversa e registra o sentimento usando um modelo multilíngue (`cardiffnlp/twitter-xlm-roberta-base-sentiment`)
* 🏆 **Ranking da comunidade** — comando `/ranking` exibe os 5 jogos mais bem avaliados com score ponderado (reviews negativas têm peso maior)
* 🎬 **GIFs contextuais** — o bot busca GIFs na Giphy com base no topic semântico mais relevante da resposta

---

<p align="center">
<img src="src/assets/brook-one-piece.gif" width="300"/>
</p>

## 🗂️ Estrutura do projeto

```bash
├── src/
│   └── telegram_bot.py       # Bot do Telegram — handlers de mensagem, voz, feedback e ranking
├── nlp_engine.py              # Motor NLP — TF-IDF + spaCy + topic map + game map
├── sentiment.py               # Análise de sentimento multilíngue (HuggingFace)
├── server.py                  # API FastAPI — emulador, saves e sessões
├── dictConfig.py              # Dicionários de configuração (FRANCHISE_HINTS, FEEDBACK_KEYWORDS, etc.)
├── game_map.json              # Mapeamento de franquias para jogos disponíveis
├── knowledge_base_en.json     # Base de conhecimento em inglês
├── knowledge_base_pt.json     # Base de conhecimento em português
├── knowledge_base_builder.py  # Script para construir a base via scraping
├── web_scraper.py             # Web scraper de wikis
├── saves.db                   # Banco SQLite (saves, sessões, feedback)
├── templates/
│   └── player.html            # Template do emulador no browser
├── roms/                      # ROMs dos jogos (não incluídas — veja nota abaixo)
│   ├── gba/
│   └── ds/
├── emulator/                  # EmulatorJS — integrado diretamente ao projeto (open source)
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

### 5. Configure as variáveis de ambiente

Crie um `.env` na raiz do projeto. Será necessário criar um bot no Telegram via **BotFather** para obter o token:

```env
TELEGRAM_TOKEN=seu_token_aqui
GIPHY_KEY=sua_chave_giphy_aqui
```

### 6. Configure as ROMs

> ⚠️ **As ROMs não estão incluídas no repositório** por questões de direitos autorais. Você precisa obtê-las por conta própria e colocá-las nas pastas corretas.

Estrutura esperada:

```bash
roms/
├── gba/
│   ├── Pokemon-Emerald.gba
│   ├── Kingdom-Hearts.gba
│   ├── Street-Fighter.gba
│   ├── MegaMan-Zero.gba
│   ├── Kirby - Nightmare in Dream Land.gba
│   ├── Sonic-Advance.gba
│   ├── Super Mario - Advance2.gba
│   └── Legend of Zelda-TheMinishCap.gba
└── ds/
    └── Pokemon-HeartGold.nds
```

Se os nomes dos arquivos forem diferentes, atualize o dicionário `games` em `server.py`.

### 7. Gere a base de conhecimento

```bash
python knowledge_base_builder.py
```

### 8. Inicie o servidor do emulador

```bash
uvicorn server:app --reload --port 8000
```

### 9. Exponha o servidor com ngrok

```bash
ngrok http 8000
```

O bot detecta automaticamente a URL pública do ngrok na inicialização.

### 10. Inicie o bot

```bash
python src/telegram_bot.py
```

---

## 🌍 Por que o ngrok?

O bot do Telegram roda localmente, mas os links dos jogos precisam ser acessíveis pelo browser do usuário — que está fora da sua máquina. O servidor FastAPI sobe em `localhost:8000`, endereço que só existe na sua rede local.

O **ngrok** resolve isso criando um túnel público temporário que aponta para o seu `localhost`. Assim, quando o bot envia um link como `https://abc123.ngrok-free.dev/play/sonic`, qualquer pessoa consegue abrir no browser e o servidor local responde normalmente.

O `nlp_engine.py` detecta automaticamente a URL pública do ngrok consultando `http://127.0.0.1:4040/api/tunnels` na inicialização — se o ngrok não estiver rodando, cai para `http://localhost:8000` como fallback.

---

## 💬 Como usar

* Envie uma pergunta em texto ou mande um áudio 🎙️
* Funciona em PT 🇧🇷 e EN 🇺🇸
* Se o assunto tiver um jogo disponível, o bot envia o link para jogar no browser
* Após jogar, mande sua opinião — o bot detecta automaticamente o sentimento
* Use `/ranking` para ver os jogos mais bem avaliados pela comunidade

**Exemplos de perguntas:**

* Quem é o Bowser?
* What are Sonic's abilities?
* Qual a história de Kingdom Hearts?
* Who is Xion?
* Quais os poderes do Kirby?

**Comandos disponíveis:**

| Comando | Descrição |
|---|---|
| `/start` | Inicia o bot e exibe instruções |
| `/ranking` | Exibe o top 5 jogos mais bem avaliados |

---

## 🧩 Categorias de perguntas suportadas

| Categoria | Exemplos |
|---|---|
| 👤 Personagens | Mario, Link, Sonic, Roxas |
| 🏢 Empresas | Nintendo, Sega, Capcom |
| 📦 Franquias | Zelda, Pokémon, Kingdom Hearts |
| 🎮 Gameplay | Mecânicas, controles |
| 📖 História | Lore, enredo |
| ⚡ Habilidades | Poderes, ataques |
| 🌍 Mundos | Hyrule, Johto, Kanto |
| 🔀 Crossovers | Aparições em outros jogos |

---

## 🏗️ Como o NLP funciona

1. **Detecção de idioma** — `langdetect` identifica PT ou EN
2. **Detecção de intenção** — keywords mapeiam a pergunta para uma categoria
3. **Extração de entidades** — spaCy extrai nomes próprios e entidades
4. **Filtragem da base** — blocos com entidades relevantes são priorizados
5. **Scoring combinado** — `0.7 × TF-IDF + 0.3 × similaridade spaCy`, com boost ×2 para blocos que contêm as entidades extraídas
6. **Deduplicação** — blocos muito similares entre si (> 0.85 de similaridade) são removidos
7. **Sugestão de jogo** — o `topic` do bloco mais forte é consultado no `topic_map`, que foi construído automaticamente na inicialização cruzando a knowledge base com o `game_map.json` e o `FRANCHISE_HINTS`

---

## 🏆 Como o ranking funciona

O ranking é alimentado automaticamente pela conversa — o usuário não precisa dar uma nota ou preencher nenhum formulário.

**O fluxo completo:**

1. O usuário abre um jogo pelo link enviado pelo bot — isso registra uma sessão em `game_sessions`
2. Na próxima vez que o usuário mandar uma mensagem no Telegram, o bot verifica se há uma sessão recente sem feedback
3. Se a mensagem contiver palavras que indiquem uma opinião (ex: "adorei", "horrível", "loved it", "boring"), o bot captura esse texto
4. O texto é passado para o modelo `cardiffnlp/twitter-xlm-roberta-base-sentiment`, que classifica o sentimento como **positive**, **negative** ou **neutral** — funciona em português e inglês
5. O resultado é salvo em `game_feedback` com o label e o score de confiança do modelo

O `/ranking` então exibe os 5 jogos com maior score, calculado como:

```
score = (positivos / (positivos + negativos × 1.5)) × log(total_reviews + 1)
```

Reviews negativas têm peso 1.5× maior que positivas. Jogos com menos de 2 reviews não entram no ranking.

---

## 🗄️ Banco de dados (SQLite)

Três tabelas em `saves.db`:

| Tabela | O que armazena |
|---|---|
| `saves` | Save files dos jogos (`.srm` e save states em base64) |
| `game_sessions` | Registro de quando cada usuário abriu cada jogo |
| `game_feedback` | Avaliações coletadas com sentimento e confiança |

---

## 📸 Screenshots

* Algumas screenshots como prévia dessa mirabolância mirabolótica

<img width="1059" height="459" alt="image" src="https://github.com/user-attachments/assets/ea97d73d-dab0-4ab6-b96f-766dd0639682" />
<img width="877" height="776" alt="image" src="https://github.com/user-attachments/assets/6bc9af0b-5570-4865-b249-25ffc978cd0a" />
<img width="1437" height="838" alt="image" src="https://github.com/user-attachments/assets/1a905c99-dd78-40e6-9786-e9b0d3cd8864" />