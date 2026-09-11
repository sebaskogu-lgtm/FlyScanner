from datetime import datetime, timedelta
from fast_flights import FlightQuery, Passengers, create_query, get_flights
import streamlit as st

st.set_page_config(page_title="Buscador Avanzado TLV", page_icon="✈️", layout="wide")

st.title("✈️ Buscador Avanzado de Vuelos (Flexible y con Detalle)")
st.write("Escanea rangos de fechas, duraciones exactas y compara aerolíneas con enlaces directos.")

# Controles de entrada avanzados
col1, col2, col3 = st.columns(3)
with col1:
    destination = st.text_input("Código IATA Destino", value="EZE", max_chars=3).upper()
with col2:
    base_date = st.date_input("Fecha Base de Salida", value=datetime.now() + timedelta(days=60))
with col3:
    flex_days = st.slider("Margen de flexibilidad (± días)", min_value=0, max_value=3, value=1)

# Selección de duraciones de viaje
st.markdown("**Duraciones de viaje preferidas (en días):**")
duration_cols = st.columns(4)
durations = []
default_durations = [7, 10, 14, 20]
for i, d in enumerate(default_durations):
    with duration_cols[i]:
        if st.checkbox(f"{d} días", value=True):
            durations.append(d)

HUBS_EUROPE = ["BCN", "MAD", "FCO"]
MIN_SAVINGS = 0.35

def generate_google_flights_link(origin, dest, dep_date, ret_date=None):
    if ret_date:
        return f"https://www.google.com/travel/flights?q=Flights%20from%20{origin}%20to%20{dest}%20on%20{dep_date}%20returning%20{ret_date}"
    return f"https://www.google.com/travel/flights?q=Flights%20from%20{origin}%20to%20{dest}%20on%20{dep_date}"

def search_flights_range(origin, dest, start_date, end_date):
    results = []
    current = start_date
    while current <= end_date:
        date_str = current.strftime("%Y-%m-%d")
        try:
            query = create_query(
                flights=[FlightQuery(date=date_str, from_airport=origin, to_airport=dest)],
                trip="one-way", seat="economy", passengers=Passengers(adults=1)
            )
            res = get_flights(query)
            if res:
                for f in res:
                    results.append({
                        "date": date_str,
                        "price": f.price,
                        "airline": getattr(f, "airline", "Varias / Desconocida"),
                        "link": generate_google_flights_link(origin, dest, date_str)
                    })
        except Exception:
            pass
        current += timedelta(days=1)
    return results

if st.button("Escanear Fechas y Combinaciones", type="primary"):
    if not durations:
        st.error("Selecciona al menos una duración de viaje.")
    else:
        start_search = base_date - timedelta(days=flex_days)
        end_search = base_date + timedelta(days=flex_days)
        
        with st.spinner(f"Analizando rango del {start_search} al {end_search} para {destination}..."):
            
            outbound_options = search_flights_range("TLV", destination, start_search, end_search)
            
            st.divider()
            st.markdown("**Resultados y Alternativas Encontradas:**")
            
            if outbound_options:
                outbound_options = sorted(outbound_options, key=lambda x: x["price"])
                for opt in outbound_options[:5]:
                    st.markdown(f"""
                    - **Fecha:** {opt['date']} | **Precio:** ${opt['price']} | **Aerolínea:** {opt['airline']}
                      * [Ver en Google Flights]({opt['link']})
                    """)
            else:
                st.warning("No se encontraron resultados directos en este rango con las restricciones actuales.")

            st.markdown("---")
            st.markdown("**Evaluación de Tramos Separados (Low Cost + Larga Distancia):**")
            
            interlining_found = False
            for hub in HUBS_EUROPE:
                leg1_opt = search_flights_range("TLV", hub, start_search, end_search)
                if leg1_opt:
                    best_leg1 = min(leg1_opt, key=lambda x: x["price"])
                    leg2_date = datetime.strptime(best_leg1['date'], "%Y-%m-%d").date()
                    leg2_opt = search_flights_range(hub, destination, leg2_date, leg2_date + timedelta(days=1))
                    if leg2_opt:
                        best_leg2 = min(leg2_opt, key=lambda x: x["price"])
                        total_price = best_leg1["price"] + best_leg2["price"]
                        interlining_found = True
                        
                        st.markdown(f"""
                        **Escala vía {hub}:** Total aproximado **${total_price}**
                        - Tramo 1 (TLV ➔ {hub}): ${best_leg1['price']} ({best_leg1['date']}) - [Enlace]({best_leg1['link']})
                        - Tramo 2 ({hub} ➔ {destination}): ${best_leg2['price']} ({best_leg2['date']}) - [Enlace]({best_leg2['link']})
                        """)
            
            if not interlining_found:
                st.info("No se hallaron combinaciones viables de tramos separados en este barrido.")
