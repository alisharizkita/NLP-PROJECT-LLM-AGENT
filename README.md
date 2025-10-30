# 🥗 FoodieBot — Intelligent Food Recommendation Agent

Rizkita Alisha Ramadhani    (22/494942/TK/54347)

Gabriella Eileen G.         (22/503523/TK/55019)

FoodieBot is an **LLM-powered intelligent agent** designed to provide **personalized food and restaurant recommendations** based on **real-time weather** and **geolocation data**.  
Built with **Python**, **Groq API**, **Discord**, **OpenWeather API**, and **Google Maps Places API**, FoodieBot offers context-aware suggestions that feel natural, human-like, and locally relevant for users in Indonesia.

---

## 🚀 Features
- 🍽️ **Contextual Recommendations** — Suggests food suited to the current weather and time (e.g., hot soup on rainy days).
- 🗺️ **Valid Restaurant Data** — Retrieves real, verifiable restaurants from Google Maps.
- 🌦️ **Weather Integration** — Uses OpenWeather API for live temperature and conditions.
- 💬 **Conversational Interface** — Interact naturally through Discord chat.
- 🧠 **Groq-Powered Reasoning** — Utilizes Groq LLM for decision-making and language generation.

---

## 🧩 System Architecture


### Components:
- **Discord**: User interaction layer.
- **Groq API**: LLM reasoning and tool-calling engine.
- **OpenWeather API**: Fetches real-time weather data.
- **Google Maps Places API**: Provides valid restaurant data.
- **Python Backend**: Orchestrates API communication and logic.

---

## 🏗️ Tech Stack

| Component | Purpose |
|------------|----------|
| **Python** | Main programming language for backend logic and API handling |
| **Discord API** | User interface via chat-based interaction |
| **Groq API** | Large Language Model for reasoning and recommendation generation |
| **OpenWeather API** | Provides weather-based contextual data |
| **Google Maps Places API** | Supplies verified restaurant data based on user’s location |

---

## ⚙️ Installation

### 1️⃣ Clone Repository
```bash
git clone https://github.com/username/foodiebot.git
cd foodiebot
```

### 2️⃣ Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```bash
