import streamlit as st
import json
import time
import random
import gspread
from google.oauth2.service_account import Credentials

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
        data["hora_inicio"],
        data["hora_fin"],
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

    seleccion = random.sample(abiertas, 6) + random.sample(cerradas, 4)
    random.shuffle(seleccion)

    return seleccion

# =====================
# APP
# =====================
st.title("Parcial Docker")

# =====================
# LOGIN ESTUDIANTE
# =====================
if "nombre" not in st.session_state:
    nombre = st.text_input("Nombre completo")

    if st.button("Iniciar examen"):
        if nombre.strip():
            st.session_state.nombre = nombre
            st.session_state.hora_inicio = time.strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.idx = 0
            st.session_state.respuestas = {}
            st.session_state.preguntas = seleccionar_preguntas()
            st.rerun()
        else:
            st.warning("Debe ingresar su nombre")

    st.stop()

# =====================
# PREGUNTAS
# =====================
i = st.session_state.idx
preguntas = st.session_state.preguntas

if i < len(preguntas):
    p = preguntas[i]

    st.subheader(f"Pregunta {i+1}")
    st.write(p["enunciado"])

    key_actual = f"resp_{i}"

    if p["tipo"] == "multiple":
        resp = st.text_input("Respuesta (A, B, C o D)", key=key_actual)
    else:
        resp = st.text_area("Respuesta", key=key_actual)

    if st.button("Siguiente"):
        if not resp.strip():
            st.warning("Debes responder antes de continuar")
        else:
            st.session_state.respuestas[p["id"]] = resp

            # limpiar input
            st.session_state.pop(key_actual, None)

            st.session_state.idx += 1
            st.rerun()

# =====================
# FINAL
# =====================
else:
    st.success("Has terminado la parte teórica")

    st.markdown("## Parte práctica")

    st.write("Ahora debes realizar la parte práctica:")

    st.link_button(
        "Ir al repositorio",
        "https://github.com/cuestamario-web/Parcial_ElectivaIII_D"
    )

    with open("parcial2.docx", "rb") as f:
        st.download_button(
            "Descargar documento práctico",
            f,
            file_name="parcial2.docx"
        )

    if st.button("Finalizar examen"):
        data = {
            "nombre": st.session_state.nombre,
            "hora_inicio": st.session_state.hora_inicio,
            "hora_fin": time.strftime("%Y-%m-%d %H:%M:%S"),
            "respuestas": st.session_state.respuestas
        }

        guardar_respuesta(data)

        st.success("Respuestas guardadas correctamente")
        st.session_state.clear()
