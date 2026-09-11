from datetime import datetime, timedelta
from fast_flights import get_flights, FlightQuery, Passengers

# Configuración base
ORIGIN = "TLV"
HUBS_EUROPE = ["BCN", "MAD", "FCO"]  # FCO (Roma), BCN, MAD
MIN_CONNECTION_HOURS = 4
SAVINGS_THRESHOLD_PERCENT = 0.35  # Exige al menos 35% de ahorro

def search_route(origin: str, destination: str, date_str: str):
    """
    Realiza la consulta real a Google Flights usando fast-flights v3.
    """
    try:
        result = get_flights(
            flight_data=[
                FlightQuery(
                    date=date_str,
                    from_airport=origin,
                    to_airport=destination,
                )
            ],
            trip="one-way",
            seat="economy",
            passengers=Passengers(adults=1),
            fetch_mode="fallback"
        )
        
        if result and result.flights:
            # Retorna el precio de la opción más económica encontrada
            cheapest = min(result.flights, key=lambda x: x.price)
            return {"price": cheapest.price, "success": True}
    except Exception as e:
        print(f"Error consultando {origin} -> {destination}: {e}")
        
    return {"price": 0, "success": False}

def evaluate_best_option(destination: str, date_str: str):
    print(f"\n--- Analizando ruta hacia {destination} para el día {date_str} ---")
    
    # 1. Buscar ruta tradicional directa o una escala
    trad = search_route(ORIGIN, destination, date_str)
    trad_price = trad["price"] if trad["success"] else 1500  fallback de seguridad
    print(f"Precio Ruta Tradicional ({ORIGIN} -> {destination}): ${trad_price}")
    
    best_interlining = None
    min_interlining_price = float('inf')
    
    # 2. Evaluar Tramos Separados vía Hubs Europeos
    for hub in HUBS_EUROPE:
        print(f"Evaluando escala en hub: {hub}...")
        
        # Tramo 1: TLV -> Hub europeo
        leg1 = search_route(ORIGIN, hub, date_str)
        if not leg1["success"]:
            continue
            
        # Tramo 2: Hub europeo -> Destino (asumiendo 1 día después o mismo día según conexión)
        # Para simplificar el script de prueba, usamos la misma fecha o ajustamos
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
        
    # Aplicar regla de ahorro
    savings = (trad_price - min_interlining_price) / trad_price
    
    if savings >= SAVINGS_THRESHOLD_PERCENT:
        print(f"¡Alerta! Tramos separados rentables via {best_interlining['hub']}. Ahorro: {savings*100:.1f}%")
        return best_interlining
    else:
        print(f"El ahorro ({savings*100:.1f}%) no justifica el riesgo. Se elige ruta tradicional.")
        return {"type": "traditional", "price": trad_price}

if __name__ == "__main__":
    # Prueba con una fecha futura de ejemplo (ej. a unos meses)
    test_destination = "EZE" 
    test_date = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
    
    best_deal = evaluate_best_option(test_destination, test_date)
    print("Resultado final seleccionado:", best_deal)
