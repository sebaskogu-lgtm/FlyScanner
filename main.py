import time
from datetime import datetime, timedelta
from fast_flights import FlightQuery, Passengers, create_query, get_flights

ORIGIN = "TLV"
HUBS_EUROPE = ["BCN", "MAD", "FCO"]
MIN_CONNECTION_HOURS = 4
SAVINGS_THRESHOLD_PERCENT = 0.35

def search_route(origin: str, destination: str, date_str: str):
    try:
        query = create_query(
            flights=[
                FlightQuery(
                    date=date_str,
                    from_airport=origin,
                    to_airport=destination,
                )
            ],
            trip="one-way",
            seat="economy",
            passengers=Passengers(adults=1)
        )
        result = get_flights(query)
        
        if result and len(result) > 0:
            cheapest = min(result, key=lambda x: x.price)
            return {"price": cheapest.price, "success": True}
    except Exception as e:
        print(f"Aviso: Google bloqueó o no devolvió datos para {origin} -> {destination}")
        
    return {"price": 0, "success": False}

def evaluate_best_option(destination: str, date_str: str):
    print(f"\n--- Analizando ruta hacia {destination} para el día {date_str} ---")
    
    trad = search_route(ORIGIN, destination, date_str)
    trad_price = trad["price"] if trad["success"] else 1500
    print(f"Precio Ruta Tradicional ({ORIGIN} -> {destination}): ${trad_price}")
    
    best_interlining = None
    min_interlining_price = float('inf')
    
    for hub in HUBS_EUROPE:
        print(f"Evaluando escala en hub: {hub}...")
        leg1 = search_route(ORIGIN, hub, date_str)
        if not leg1["success"]:
            continue
            
        leg2 = search_route(hub, destination, date_str)
        if not leg2["success"]:
            continue
            
        total_price = leg1["price"] + leg2["price"]
        print(f"  -> Via {hub}: Tramo1 (${leg1['price']}) + Tramo2 (${leg2['price']}) = Total: ${total_price}")
        
        if total_price < min_interlining_price:
            min_interlining_price = total_price
            best_interlining = {"hub": hub, "price": total_price, "type": "virtual_interlining"}

    if not best_interlining:
        print("No se pudieron calcular combinaciones de tramos separados.")
        return {"type": "traditional", "price": trad_price}
        
    savings = (trad_price - min_interlining_price) / trad_price
    
    if savings >= SAVINGS_THRESHOLD_PERCENT:
        print(f"¡Alerta! Tramos separados rentables via {best_interlining['hub']}. Ahorro: {savings*100:.1f}%")
        return best_interlining
    else:
        print(f"El ahorro ({savings*100:.1f}%) no justifica el riesgo.")
        return {"type": "traditional", "price": trad_price}

if __name__ == "__main__":
    test_destination = "EZE" 
    test_date = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
    
    while True:
        evaluate_best_option(test_destination, test_date)
        print("\n[Worker] Esperando 12 horas para la siguiente verificación...")
        time.sleep(43200)  # Duerme 12 horas (43200 segundos) para evitar bloqueos masivos de Google
