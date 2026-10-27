# 🍽️ Food Verse AI

> **Multimodal Food Intelligence Agent** — Powered by Gemini & Groq LLMs

[![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)

Food Verse AI is an intelligent, multimodal food assistant that uses vision-language models to analyze food images, check freshness, audit kitchen hygiene, suggest recipes from your pantry, and build personalized weekly meal plans.

---

## ✨ Features

| Module | Description |
|--------|-------------|
| 🍛 **Nutrition Audit** | Upload a meal photo → get dish name, calories, macros, allergens & health score |
| 🥬 **Freshness Check** | Diagnose freshness of fruits, vegetables, meat or dairy from a photo |
| 🧼 **Kitchen Hygiene** | Audit kitchen images/videos for food safety compliance violations |
| 👩‍🍳 **Recipe Assistant** | Enter your pantry ingredients → get creative, diet-aware recipes |
| 📅 **Meal Planner** | Input your profile → receive a personalized 7-day meal plan with grocery list |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- A **Gemini** or **Groq** API key *(optional — Demo mode works without one)*

### Installation

```bash
# Clone the repository
git clone https://github.com/nehaseijwani04-aj/Food-Verse.git
cd Food-Verse

# Create a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The app will open at **http://localhost:8501**

---

## 🔑 API Keys

Food Verse AI supports two AI providers:

| Provider | Model | Get Key |
|----------|-------|---------|
| **Gemini** | `gemini-2.0-flash` (default) | [aistudio.google.com](https://aistudio.google.com/app/apikey) |
| **Groq** | `meta-llama/llama-4-scout-17b-16e-instruct` (default) | [console.groq.com](https://console.groq.com/keys) |

> 💡 No API key? Select **"Demo (no key)"** in the sidebar — all features work with sample data!

---

## 🧰 Tech Stack

- **[Streamlit](https://streamlit.io)** — UI framework
- **[Google Generative AI](https://ai.google.dev)** — Gemini vision models
- **[Groq](https://groq.com)** — Ultra-fast LLM inference
- **[Plotly](https://plotly.com)** — Interactive charts
- **[Pillow](https://python-pillow.org)** — Image processing
- **[OpenCV](https://opencv.org)** — Video frame extraction

---

## 📦 Dependencies

```
streamlit>=1.36
plotly>=5.20
pillow>=10.0
google-generativeai>=0.7
groq>=0.9
opencv-python-headless>=4.9
```

---

## ⚠️ Disclaimer

Food Verse AI provides **informational estimates only** and is **not a substitute for professional medical or nutritional advice**. Always consult a qualified professional for dietary decisions.

---

## 📄 License

This project is licensed under the MIT License.

---

<p align="center">Made with ❤️ · Food Verse AI · Skill Wallet Capstone 3</p>
