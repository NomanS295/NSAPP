# NSAPP
Personal app to  find cheapest flights from toronto using google flights and kiwi.com (for now) with mullvad VPN  geo-switching

vibecoded a locally-run AI-powered deal finder built for Toronto (YYZ) departures. 

## Features
- Searches Google Flights + Kiwi.com simultaneously
- Mullvad VPN cycling through multiple countries to beat geo-pricing
- AI chat assistant powered by local Llama model (no cloud, no subscriptions)
- Clean Gradio web UI accessible from your browser

## Tech Stack
- Python + Gradio (UI)
- llama.cpp (local AI server)
- Qwen3.5 35B GGUF model via Ollama
- SerpApi (Google Flights)
- Kiwi.com via RapidAPI
- Mullvad VPN for geo-switching

## Setup
1. Clone the repo
2. Copy `config.example.py` to `config.py` and add your API keys
3. Start your llama.cpp server
4. Run `pip install -r requirements.txt`
5. Run `python app.py`
6. Open `http://127.0.0.1:7860`

## Requirements
- Python 3.10+
- llama.cpp running locally
- SerpApi key
- RapidAPI key (Kiwi.com)
- Mullvad VPN (optional, for geo-pricing)

## Known Issues / Work In Progress

### Why no proper calendar picker?
The app uses Gradio for the UI, which has a built-in DateTime component but it returns 
Unix timestamps instead of formatted dates, causing the flight search to break. We tried 
embedding a custom HTML calendar inside Gradio and syncing it to hidden input fields, but 
Gradio's component system makes it difficult to pass values from raw HTML elements back to 
Python functions reliably — the JavaScript can't consistently target Gradio's internal 
input elements across different component ID assignments.

The fix is to either:
1. Build a proper frontend in React or plain HTML/CSS/JS that calls a Python backend API
2. Wait for better Gradio DateTime support
3. Use Streamlit instead of Gradio which has better date picker support

For now, manual text input (YYYY-MM-DD) works reliably and is the simplest solution.
### Geo-Pricing (VPN)
Mullvad VPN is integrated and switching between countries (Mexico, Singapore, Turkey, Poland) 
is confirmed working — but Google Flights and Kiwi.com return identical prices regardless of 
IP location. Airlines appear to price YYZ departures the same globally. Still investigating 
whether a different data source could expose geo-based pricing differences.


### Skyscanner Integration
Attempted integration via SerpApi (no Skyscanner engine available), Sky-Scrapper RapidAPI 
(proxy failures), and official Skyscanner API (business partners only). Currently using 
Google Flights + Kiwi.com as dual sources. Open to suggestions for a reliable Skyscanner 
data source.


