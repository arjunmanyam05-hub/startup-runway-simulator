# 📈 Startup Runway & Growth Simulator

An interactive financial dashboard that visualizes startup health and lets you simulate what happens when key assumptions change.

Built as a portfolio/networking tool by Arjun Manyam

## What it does

- Generates a realistic 24-month synthetic startup dataset (B2B SaaS model with a Series A at Month 12)
- Displays core metrics: Revenue, Burn, Net Burn, Cash on Hand, Runway
- 5 interactive charts: Revenue, Burn Rate, Cash Balance, Runway Risk, Revenue vs Burn
- Scenario sliders: adjust revenue and burn assumptions → all charts and metrics update instantly
- Quick scenario presets: Strong Growth, Efficient Mode, Slowdown, Crisis

## Run locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Launch the app
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

## Deploy to Streamlit Cloud (free)

1. Push this folder to a GitHub repo
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo, set `app.py` as the entry point
4. Click Deploy — you'll get a shareable URL in ~2 minutes

## Project structure

```
startup_simulator/
├── app.py            # Main Streamlit dashboard
├── data.py           # Dataset generation and scenario logic
├── requirements.txt  # Python dependencies
└── README.md
```

## Tech stack

- **Python** — data logic
- **Streamlit** — interactive web app framework
- **Plotly** — charts
- **pandas / numpy** — data manipulation

## Conversation starter pitch

> "I built a small tool that simulates startup financial health — you can drag sliders to see what happens to runway if revenue slows 25% or if a hiring spree increases burn. Happy to walk you through it if you have 5 minutes."
# streamlit-code
