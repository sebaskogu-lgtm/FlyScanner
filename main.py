from datetime import datetime, timedelta
# Importación conceptual de la librería open-source para extraer Google Flights sin API de pago
# pip install fast-flights
from fast_flights import FlightData, Passengers, Result

# Configuración base
ORIGIN = "TLV"
HUBS_EUROPE = ["BCN", "MAD", "ROM"]  # BCN clave para LEVEL, MAD para Plus Ultra/World2Fly
MIN_CONNECTION_HOURS = 4
SAVINGS_THRESHOLD_PERCENT = 0.35  # Exige al menos 35% de ahorro para arriesgar tickets separados

def search_traditional_route(destination: str, date_range: tuple):
    """
    Busca la ruta tradicional directa/una escala (ej. Ethiopian, ITA).
    Devuelve el precio piso de seguridad.
    """
    print(f"Buscando ruta tradicional {ORIGIN} -> {destination}...")
    # Implementación con fast-flights para obtener el precio consolidado
    # result = FlightData(origin=ORIGIN, destination=destination, date=date_range[0], ...)
    # Retorna un diccionario con precio mínimo y aerolínea
    return {"price": 1200, "airline": "Traditional", "type": "direct/single-ticket"}

def search_virtual_interlining(destination: str, hubs: list, date_range: tuple):
    """
    Busca la combinación de tramos separados:
    Tramo 1: TLV -> Hub Europeo (Wizz Air / Ryanair)
    Tramo 2: Hub Europeo -> Destino (LEVEL / Long-haul low cost)
    """
    combinations = []
    
    for hub in hubs:
        print(f"Evaluando tramo 1: {ORIGIN} -> {hub}...")
        # Simulación de extracción de vuelo corto
        short_haul_price = 150  
        short_haul_arrival_time = datetime.now() + timedelta(hours=4)
        
        print(f"Evaluando tramo 2: {hub} -> {destination} (ej. LEVEL)...")
        # Simulación de extracción de vuelo largo
        long_haul_price = 650
        long_haul_departure_time = short_haul_arrival_time + timedelta(hours=5) # 5 horas de escala
        
        # Filtro estricto de tiempo de escala
        connection_time = (long_haul_departure_time - short_haul_arrival_time).total_seconds() / 3600
        if connection_time < MIN_CONNECTION_HOURS:
            continue # Descartar por riesgo de pérdida
            
        total_price = short_haul_price + long_haul_price
        combinations.append({
            "hub": hub,
            "price": total_price,
            "type": "virtual_interlining",
            "scale_hours": connection_time
        })
        
    if not combinations:
        return None
    
    # Retorna la opción más barata de interlining
    return min(combinations, key=lambda x: x["price"])

def evaluate_best_option(destination: str, date_range: tuple):
    traditional = search_traditional_route(destination, date_range)
    interlining = search_virtual_interlining(destination, HUBS_EUROPE, date_range)
    
    if not interlining:
        return traditional
        
    # Aplicar regla de umbral de ahorro
    savings = (traditional["price"] - interlining["price"]) / traditional["price"]
    
    if savings >= SAVINGS_THRESHOLD_PERCENT:
        print(f"¡Alerta! Tramos separados rentables via {interlining['hub']}. Ahorro: {savings*100:.1f}%")
        return interlining
    else:
        print("El ahorro no justifica el riesgo de tickets separados. Se elige ruta tradicional.")
        return traditional

# Ejemplo de ejecución
if __name__ == "__main__":
    dest = "EZE" # o "TYO"
    dates = ("2026-10-01", "2026-10-20")
    best_deal = evaluate_best_option(dest, dates)
    print("Resultado final:", best_deal)
