import streamlit as st
import json
import time
import random
import gspread
from google.oauth2.service_account import Credentials

TIEMPO_EXAMEN = 60 * 30

# =====================
# GOOGLE SHEETS
# =====================
def conectar_sheets():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    return client.open("respuestas_parcial").sheet1

def guardar_respuesta(data):
    sheet = conectar_sheets()
    sheet.append_row([
        data["nombre"],
        data["fecha"],
        json.dumps(data["respuestas"])
    ])

# =====================
# CARGAR PREGUNTAS
# =====================
def cargar_preguntas():
    with open("preguntas.json", "r", encoding="utf-8") as f:
        return json.load(f)

# =====================
# SELECCIÓN ALEATORIA
# =====================
def seleccionar_preguntas():
    todas = cargar_preguntas()
    abiertas = [p for p in todas if p["tipo"] == "abierta"]
    cerradas = [p for p in todas if p["tipo"] == "multiple"]

    return random.sample(abiertas, 6) + random.sample(cerradas, 4)

# =====================
# APP
# =====================
st.title("Parcial Docker")

if "nombre" not in st.session_state:
    nombre = st.text_input("Nombre completo")

    if st.button("Iniciar"):
        if nombre.strip():
            st.session_state.nombre = nombre
            st.session_state.start = time.time()
            st.session_state.idx = 0
            st.session_state.respuestas = {}
            st.session_state.preguntas = seleccionar_preguntas()
            st.rerun()
    st.stop()

# =====================
# CRONÓMETRO
# =====================
tiempo = TIEMPO_EXAMEN - (time.time() - st.session_state.start)

if tiempo <= 0:
    st.warning("Tiempo terminado")
    finalizar = True
else:
    mins, secs = divmod(int(tiempo), 60)
    st.info(f"Tiempo restante: {mins:02d}:{secs:02d}")
    finalizar = False

# =====================
# PREGUNTAS
# =====================
i = st.session_state.idx
preguntas = st.session_state.preguntas

if not finalizar and i < len(preguntas):
    p = preguntas[i]

    st.subheader(f"Pregunta {i+1}")
    st.write(p["enunciado"])

    if p["tipo"] == "multiple":
        resp = st.text_input("Respuesta (A,B,C,D)")
    else:
        resp = st.text_area("Respuesta")

    if st.button("Siguiente"):
        if not resp.strip():
            st.warning("Debes responder")
        else:
            st.session_state.respuestas[p["id"]] = resp
            st.session_state.idx += 1
            st.rerun()

# =====================
# FINAL
# =====================
else:
    st.success("Has terminado la parte teórica")

    st.markdown("## Parte práctica")

    st.link_button("Ir al repositorio", "https://github.com/cuestamario-web/Parcial_ElectivaIII_D")

    with open("parcial2.docx", "rb") as f:
        st.download_button("Descargar documento práctico", f, file_name="parcial2.docx")

    if st.button("Finalizar examen"):
        data = {
            "nombre": st.session_state.nombre,
            "fecha": time.strftime("%Y-%m-%d %H:%M:%S"),
            "respuestas": st.session_state.respuestas
        }

        guardar_respuesta(data)

        st.success("Respuestas guardadas correctamente")
        st.session_state.clear()
