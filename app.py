from datetime import datetime, timedelta
from fast_flights import FlightQuery, Passengers, create_query, get_flights
import streamlit as st

st.set_page_config(
    page_title="Buscador de Vuelos TLV", page_icon="✈️", layout="centered"
)

st.title("✈️ Buscador Inteligente de Vuelos desde TLV")
st.write(
    "Compara rutas tradicionales frente a tramos separados usando aerolíneas"
    " low cost."
)

# Panel de entradas interactivo
col1, col2 = st.columns(2)
with col1:
  destination = st.text_input(
      "Código IATA de Destino", value="EZE", max_chars=3
  ).upper()
with col2:
  travel_date = st.date_input(
      "Fecha de vuelo", value=datetime.now() + timedelta(days=60)
  )

date_str = travel_date.strftime("%Y-%m-%d")
HUBS_EUROPE = ["BCN", "MAD", "FCO"]
MIN_SAVINGS = 0.35


def search_route(origin: str, destination: str, date_str: str):
  try:
    query = create_query(
        flights=[
            FlightQuery(
                date=date_str, from_airport=origin, to_airport=destination
            )
        ],
        trip="one-way",
        seat="economy",
        passengers=Passengers(adults=1),
    )
    result = get_flights(query)
    if result and len(result) > 0:
      cheapest = min(result, key=lambda x: x.price)
      return {"price": cheapest.price, "success": True}
  except Exception:
    pass
  return {"price": 0, "success": False}


if st.button("Buscar y Analizar Rutas", type="primary"):
  with st.spinner(f"Consultando vuelos hacia {destination} para el {date_str}..."):

    # Ruta tradicional
    trad = search_route("TLV", destination, date_str)
    trad_price = trad["price"] if trad["success"] else 1500

    # Tramos separados
    best_interlining = None
    min_interlining_price = float("inf")
    hub_details = []

    for hub in HUBS_EUROPE:
      leg1 = search_route("TLV", hub, date_str)
      if not leg1["success"]:
        continue
      leg2 = search_route(hub, destination, date_str)
      if not leg2["success"]:
        continue

      total = leg1["price"] + leg2["price"]
      hub_details.append(
          {"hub": hub, "leg1": leg1["price"], "leg2": leg2["price"], "total": total}
      )
      if total < min_interlining_price:
        min_interlining_price = total
        best_interlining = {"hub": hub, "price": total}

    # Mostrar Resultados visuales
    st.divider()
    col_a, col_b = st.columns(2)

    with col_a:
      st.metric(
          label="Ruta Tradicional (Directa/Escala única)",
          value=f"${trad_price}",
      )

    if best_interlining:
      savings = (trad_price - min_interlining_price) / trad_price
      with col_b:
        st.metric(
            label=f"Mejor Interlining (Vía {best_interlining['hub']})",
            value=f"${min_interlining_price}",
            delta=f"-{savings*100:.1f}%",
        )

      if savings >= MIN_SAVINGS:
        st.success(
            f"¡Conviene volar separado vía {best_interlining['hub']}! El ahorro"
            f" supera el {MIN_SAVINGS*100}%."
        )
      else:
        st.warning(
            "El ahorro con tramos separados no justifica el riesgo de perder"
            " la conexión."
        )

      st.subheader("Desglose de escalas evaluadas:")
      for h in hub_details:
        st.write(
            f"- **{h['hub']}**: TLV ➔ {h['hub']} (${h['leg1']}) + {h['hub']} ➔"
            f" {destination} (${h['leg2']}) = **Total: ${h['total']}**"
        )
    else:
      st.error(
          "No se pudieron calcular combinaciones de tramos separados para esta"
          " fecha."
      )
