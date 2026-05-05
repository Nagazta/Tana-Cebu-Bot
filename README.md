# 🌴 TanaCebu Bot

> **Your kauban sa suroy!** — A Facebook Messenger chatbot for Cebu tourism, powered by Flask + Google Gemini AI.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🤖 AI Responses | Powered by Google Gemini (`gemini-1.5-flash`) |
| 🌊 Quick Replies | Beaches, Food, Spots buttons for easy navigation |
| ⌨️ Typing Indicator | Shows "typing…" while the bot thinks |
| 🔒 Secure Secrets | All tokens stored in `.env` (never in code) |
| 📝 Logging | Console + `tana_cebu.log` file |
| 💬 Long Message Support | Auto-splits replies over 2000 characters |
| 🚀 Health Check | `GET /` returns bot status |

---

## 📁 Project Structure

```
TanaCebu-Bot/
├── app.py              # Main Flask app
├── requirements.txt    # Python dependencies
├── .env.example        # Template — copy to .env and fill in values
├── .env                # Your secrets (DO NOT commit this!)
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone / Open the project

```bash
cd TanaCebu-Bot
```

### 2. Create a virtual environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

```bash
copy .env.example .env       # Windows
# cp .env.example .env       # macOS / Linux
```

Open `.env` and fill in your real values:

```env
PAGE_ACCESS_TOKEN=your_facebook_page_access_token_here
VERIFY_TOKEN=any_secret_string_you_choose
GEMINI_API_KEY=your_gemini_api_key_here
```

### 5. Run the bot locally

```bash
python app.py
```

The server starts at `http://localhost:5000`.

---

## 🌐 Exposing Localhost to the Internet (for Testing)

Facebook requires a **public HTTPS URL** for webhooks. Use **ngrok** while testing locally:

```bash
# Install ngrok → https://ngrok.com/download
ngrok http 5000
```

Copy the `https://xxxx.ngrok-free.app` URL — you'll need it in Meta's dashboard.

---

## ⚙️ Facebook Developer Setup

### Step 1 — Create a Meta App
1. Go to [developers.facebook.com](https://developers.facebook.com/) → **My Apps → Create App**
2. Choose **Business** type, name it **TanaCebu**

### Step 2 — Add Messenger Product
1. In your app dashboard → **Add Product → Messenger**
2. Under **Access Tokens**, select or create a Facebook Page and generate a **Page Access Token**
3. Copy the token into your `.env` as `PAGE_ACCESS_TOKEN`

### Step 3 — Configure the Webhook
1. In Messenger Settings → **Webhooks → Configure**
2. **Callback URL**: `https://your-ngrok-url.ngrok-free.app/webhook`
3. **Verify Token**: paste the same string you put in `.env` as `VERIFY_TOKEN`
4. **Subscription Fields**: tick `messages` and `messaging_postbacks`
5. Click **Verify and Save** — the bot's `verify_webhook()` will respond automatically

### Step 4 — Subscribe to your Page
Under Webhooks → **Add Subscriptions**, select your page and tick `messages`.

### Step 5 — Set Get Started Button (optional but recommended)
Run this once with curl or Postman:

```bash
curl -X POST "https://graph.facebook.com/v19.0/me/messenger_profile" \
  -H "Content-Type: application/json" \
  -d '{"get_started": {"payload": "GET_STARTED"}}' \
  "?access_token=YOUR_PAGE_ACCESS_TOKEN"
```

This triggers the intro message with Quick Reply buttons when a user first opens the chat.

---

## 🌴 Bot Personality

TanaCebu speaks casually, mixes **English + Cebuano (Bisaya)**, and uses emojis.  
It recommends real Cebu destinations:

| Type | Examples |
|---|---|
| 🏖️ Beaches | Bantayan Island, Moalboal, Malapascua, Sumilon |
| 🍖 Food | Lechon, Sutukil, Ngohiong, Puso |
| 📍 Spots | Kawasan Falls, Temple of Leah, Simala Shrine, Tops |

---

## 🔑 Getting API Keys

| Key | Where to get it |
|---|---|
| `GEMINI_API_KEY` | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) |
| `PAGE_ACCESS_TOKEN` | Meta Developer App → Messenger → Token Generation |
| `VERIFY_TOKEN` | You choose this — any random string |

---

## ☁️ Deploying to Production

Popular free/cheap options:

| Platform | Notes |
|---|---|
| **Render** | Free tier, easy GitHub deploy |
| **Railway** | Simple, fast, free allowance |
| **Heroku** | Classic PaaS |
| **Google Cloud Run** | Scales to zero, generous free tier |

Set your environment variables in the platform's dashboard (not in `.env`).

---

## 📜 License

MIT — feel free to fork and extend for other Philippine tourism bots!
