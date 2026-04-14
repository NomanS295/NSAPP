import gradio as gr
from openai import OpenAI
from tools.flights import search_flights
from config import SERPAPI_KEY, LLAMA_URL, RAPIDAPI_KEY

client = OpenAI(base_url=LLAMA_URL, api_key="not-needed")

def ask_ai(message, history):
    messages = [
        {"role": "system", "content": "You are NSAPP, a personal deal hunter assistant for Noman. You help find cheap flights from Toronto (YYZ), deals in Toronto, and general life recommendations. Be concise, friendly and helpful."}
    ]
    for h in history:
        messages.append({"role": "user", "content": h[0]})
        messages.append({"role": "assistant", "content": h[1]})
    messages.append({"role": "user", "content": message})
    response = client.chat.completions.create(
        model="local",
        messages=messages,
        stream=True
    )
    result = ""
    for chunk in response:
        if chunk.choices[0].delta.content:
            result += chunk.choices[0].delta.content
            yield result

def find_flights(destination, outbound_date, return_date):
    try:
        if not destination:
            return "Please enter a destination airport code."
        if not outbound_date or not return_date:
            return "Please select both departure and return dates."
        flights = search_flights(destination.upper(), outbound_date, return_date, SERPAPI_KEY, RAPIDAPI_KEY)
        if not flights:
            return "No flights found. Try different dates or destination."
        result = f"## Flights YYZ to {destination.upper()}\n"
        result += f"*Searched Google Flights + Kiwi.com*\n\n"
        for i, f in enumerate(flights, 1):
            medal = "1st" if i == 1 else "2nd" if i == 2 else "3rd" if i == 3 else f"#{i}"
            result += f"---\n"
            result += f"### {medal} {f['price']} - {f['airline']} ({f['source']})\n"
            result += f"- Departs: {f['departs']} | Arrives: {f['arrives']}\n"
            result += f"- Duration: {f['duration']}\n"
            result += f"- Stops: {f['stops']} ({f['stop_cities']})\n"
            result += f"- Flights: {f['flight_numbers']}\n"
            result += f"- Found from: {f['found_from']}\n\n"
        return result
    except Exception as e:
        return f"Error: {str(e)}"

with gr.Blocks(title="NSAPP") as app:
    gr.Markdown("# NSAPP - Your Personal Deal Hunter")
    with gr.Tabs():
        with gr.Tab("AI Chat"):
            gr.ChatInterface(
                fn=ask_ai,
                chatbot=gr.Chatbot(height=500),
                textbox=gr.Textbox(placeholder="Ask me anything...", scale=7),
            )
        with gr.Tab("Flight Finder"):
            gr.Markdown("### Cheapest Flights from Toronto YYZ")
            dest = gr.Textbox(label="Destination Airport Code", placeholder="LAX, JFK, LHR, DXB...")
            with gr.Row():
                out_date = gr.Textbox(label="Departure Date", placeholder="2026-08-01", info="Format: YYYY-MM-DD")
                ret_date = gr.Textbox(label="Return Date", placeholder="2026-08-14", info="Format: YYYY-MM-DD")
            search_btn = gr.Button("Find Best Deals", variant="primary", size="lg")
            flight_output = gr.Markdown()
            search_btn.click(find_flights, inputs=[dest, out_date, ret_date], outputs=flight_output)

app.launch(inbrowser=True)