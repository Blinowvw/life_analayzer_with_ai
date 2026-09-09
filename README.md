# 🏠 RealEstate Mentor Bot — AI Financial Advisor for Housing

> *Russian-language Telegram bot that replaces a realtor and financial advisor. It analyzes your income, savings, and helps you choose between a mortgage or renting + investing.*

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?logo=telegram)
![AI](https://img.shields.io/badge/LLM-Russian--optimized-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 🎯 How It Works — Visual Walkthrough

Here's what the user sees when talking to the bot:

### 1️⃣ Start the conversation
The bot introduces itself and explains its purpose clearly.

![Start Screen](screenshots/1_start.png)

---

### 2️⃣ Income question
It asks for monthly net income to calculate affordability.

![Income Question](screenshots/2_income.png)

---

### 3️⃣ Savings & Down Payment
The bot collects your current savings to evaluate the down payment potential.

![Savings Question](screenshots/3_savings.png)

---

### 4️⃣ Final Recommendation
The AI generates a personalized financial plan — **buy, rent, or wait**.

![Final Result](screenshots/4_result.png)

> 💡 *In this example, the bot recommended "Rent + Invest" because the mortgage payment exceeded 40% of income.*

---

## 🌟 Concept & Mission

Most people struggle with the biggest financial decision of their lives: **"Should I buy a home or rent and invest the difference?"**

This bot is not just a calculator. It is a **decision-making engine** that:
- Asks targeted questions about your monthly income, current savings, and lifestyle.
- Uses a built-in Russian AI model to simulate financial scenarios.
- Provides a clear, actionable recommendation: **Mortgage** vs. **Rent + Invest**.
- Explains the logic behind the advice in plain Russian.

**The goal:** To democratize financial planning and give everyone access to a personal data-driven advisor, completely for free.

---

## 🧠 How It Works (The "Invention")

Unlike standard mortgage calculators, this bot uses a **proprietary heuristic + LLM hybrid** logic:

1. **Data Collection** — The bot asks in a structured dialogue:
   - Monthly net income (₽)
   - Total savings / down payment (₽)
   - City / Region (for cost-of-living adjustment)
   - Current monthly rent (₽)

2. **Core Analysis** — The engine calculates:
   - Maximum affordable mortgage payment (based on the 40% income rule).
   - Opportunity cost of using savings as a down payment vs. investing it.
   - Projected property appreciation vs. stock market returns (conservative estimates).

3. **AI Synthesis** — The embedded Russian LLM formats the raw numbers into a human-readable, empathetic, and structured financial plan. It doesn't just give numbers; it gives **life advice**.

4. **Decision Matrix**:
   - ✅ **"Buy Now"** — if mortgage payment ≈ rent + 15% and savings cover 20% down payment.
   - ⚠️ **"Rent & Invest"** — if your city has a low price-to-rent ratio or high market uncertainty.
   - 🛑 **"Wait & Accumulate"** — if you lack sufficient down payment or income stability.

---

## 📦 Tech Stack

| Component | Technology |
|-----------|------------|
| **Framework** | `python-telegram-bot` v20+ |
| **AI Core** | Custom Russian fine-tuned LLM (via Transformers / Ollama) |
| **State Machine** | Built-in `ConversationHandler` |
| **Data Layer** | SQLite (local) / PostgreSQL (optional) |
| **Deployment** | Docker + NGINX + Gunicorn |

---

## 🚀 Quick Start (for Developers)

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/realestate-mentor-bot.git
cd realestate-mentor-bot

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
echo "BOT_TOKEN=your_telegram_token" > .env
echo "AI_MODEL_PATH=./models/ru_advisor" >> .env

# 5. Run the bot
python bot.py
