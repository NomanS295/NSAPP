import requests
import subprocess
import time
from datetime import datetime

SEARCH_COUNTRIES = [
    {"code": None,  "label": "Canada (default)"},
    {"code": "mx",  "label": "Mexico"},
    {"code": "sg",  "label": "Singapore"},
    {"code": "tr",  "label": "Turkey"},
    {"code": "pl",  "label": "Poland"},
]

def format_date(date_val):
    if date_val is None:
        return ""
    try:
        return datetime.fromtimestamp(float(date_val)).strftime("%Y-%m-%d")
    except:
        pass
    date_str = str(date_val)
    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
        try:
            return datetime.strptime(date_str.split(".")[0], fmt).strftime("%Y-%m-%d")
        except:
            continue
    return date_str.split(" ")[0]

def switch_vpn(country_code):
    if country_code is None:
        subprocess.run(["mullvad", "disconnect"], capture_output=True)
        time.sleep(3)
    else:
        subprocess.run(["mullvad", "relay", "set", "location", country_code], capture_output=True)
        subprocess.run(["mullvad", "connect"], capture_output=True)
        time.sleep(5)

def search_google_flights(destination, out_str, ret_str, serpapi_key):
    flights = []
    for country in SEARCH_COUNTRIES:
        try:
            switch_vpn(country["code"])
            params = {
                "engine": "google_flights",
                "departure_id": "YYZ",
                "arrival_id": destination,
                "outbound_date": out_str,
                "return_date": ret_str,
                "currency": "CAD",
                "hl": "en",
                "api_key": serpapi_key
            }
            response = requests.get("https://serpapi.com/search", params=params)
            data = response.json()
            for result in data.get("best_flights", [])[:3]:
                first_flight = result["flights"][0]
                last_flight = result["flights"][-1]
                layovers = result.get("layovers", [])
                flights.append({
                    "source": "Google Flights",
                    "price_raw": result.get("price", 99999),
                    "price": f"CAD ${result.get('price')}",
                    "airline": first_flight.get("airline"),
                    "duration": f"{result.get('total_duration')} mins",
                    "stops": len(result.get("flights", [])) - 1,
                    "stop_cities": " -> ".join([l["name"].split(" ")[0] for l in layovers]) if layovers else "Direct",
                    "departs": first_flight["departure_airport"].get("time", ""),
                    "arrives": last_flight["arrival_airport"].get("time", ""),
                    "flight_numbers": ", ".join([f["flight_number"] for f in result["flights"]]),
                    "legroom": first_flight.get("legroom", "N/A"),
                    "found_from": country["label"],
                    "carbon": result.get("carbon_emissions", {}).get("difference_percent", 0)
                })
        except Exception as e:
            print(f"  Google error {country['label']}: {e}")
    subprocess.run(["mullvad", "disconnect"], capture_output=True)
    return flights

def search_kiwi_flights(destination, out_str, ret_str, rapidapi_key):
    flights = []
    try:
        headers = {
            "x-rapidapi-host": "kiwi-com-cheap-flights.p.rapidapi.com",
            "x-rapidapi-key": rapidapi_key
        }
        out_dt = datetime.strptime(out_str, "%Y-%m-%d")
        ret_dt = datetime.strptime(ret_str, "%Y-%m-%d")
        params = {
            "source": "Airport:YYZ",
            "destination": f"Airport:{destination}",
            "currency": "cad",
            "locale": "en",
            "adults": "1",
            "cabinClass": "ECONOMY",
            "sortBy": "PRICE",
            "sortOrder": "ASCENDING",
            "transportTypes": "FLIGHT",
            "outboundDepartureDateStart": out_dt.strftime("%Y-%m-%dT00:00:00"),
            "outboundDepartureDateEnd": out_dt.strftime("%Y-%m-%dT23:59:59"),
            "inboundDepartureDateStart": ret_dt.strftime("%Y-%m-%dT00:00:00"),
            "inboundDepartureDateEnd": ret_dt.strftime("%Y-%m-%dT23:59:59"),
            "limit": "10"
        }
        response = requests.get(
            "https://kiwi-com-cheap-flights.p.rapidapi.com/round-trip",
            headers=headers,
            params=params
        )
        data = response.json()
        itineraries = data.get("itineraries", [])
        for result in itineraries[:5]:
            price_raw = int(float(result.get("price", {}).get("amount", 99999)))
            outbound = result.get("outbound", {})
            segments = outbound.get("sectorSegments", [])
            airline = "Unknown"
            departs = ""
            arrives = ""
            flight_numbers = []
            stop_cities = []
            stops = max(0, len(segments) - 1)
            if segments:
                first_seg = segments[0].get("segment", {})
                last_seg = segments[-1].get("segment", {})
                airline = first_seg.get("carrier", {}).get("name", "Unknown")
                departs = first_seg.get("source", {}).get("localTime", "").replace("T", " ")
                arrives = last_seg.get("destination", {}).get("localTime", "").replace("T", " ")
                for s in segments:
                    seg = s.get("segment", {})
                    carrier_code = seg.get("carrier", {}).get("code", "")
                    flight_code = seg.get("code", "")
                    flight_numbers.append(f"{carrier_code}{flight_code}")
                for s in segments[1:]:
                    seg = s.get("segment", {})
                    city = seg.get("source", {}).get("station", {}).get("city", {}).get("name", "")
                    if city:
                        stop_cities.append(city)
            duration_mins = outbound.get("duration", 0) // 60
            flights.append({
                "source": "Kiwi.com",
                "price_raw": price_raw,
                "price": f"CAD ${price_raw}",
                "airline": airline,
                "duration": f"{duration_mins} mins",
                "stops": stops,
                "stop_cities": " -> ".join(stop_cities) if stop_cities else "Direct",
                "departs": departs,
                "arrives": arrives,
                "flight_numbers": ", ".join(flight_numbers),
                "legroom": "N/A",
                "found_from": "Kiwi.com",
                "carbon": 0
            })
    except Exception as e:
        print(f"  Kiwi error: {e}")
    return flights

def search_flights(destination, outbound_date, return_date, serpapi_key, rapidapi_key=None):
    out_str = format_date(outbound_date)
    ret_str = format_date(return_date)
    print(f"Searching YYZ to {destination} | {out_str} to {ret_str}")
    all_flights = []
    print("  Searching Google Flights...")
    all_flights.extend(search_google_flights(destination, out_str, ret_str, serpapi_key))
    if rapidapi_key:
        print("  Searching Kiwi.com...")
        all_flights.extend(search_kiwi_flights(destination, out_str, ret_str, rapidapi_key))
    seen = set()
    unique_flights = []
    for f in all_flights:
        key = (f["price_raw"], f["airline"])
        if key not in seen:
            seen.add(key)
            unique_flights.append(f)
    unique_flights.sort(key=lambda x: x["price_raw"])
    return unique_flights[:15]
