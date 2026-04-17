import streamlit as st
import json
import random
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# =========================
# CONFIG
# =========================
SPREADSHEET_ID = "1NEf7T8t3rLWA1osPmmu6JE4EG15FE89E46vIZUcSB5c"

# =========================
# CONEXION GOOGLE SHEETS
# =========================
def conectar_sheets():
    creds = Credentials.from_service_account_info(
        json.loads(st.secrets["gcp_service_account"]["json"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID).sheet1

sheet = conectar_sheets()

# =========================
# UTILIDADES
# =========================
def normalizar_texto(texto):
    return texto.strip().lower()

def normalizar_fila(fila):
    return {k.strip().lower(): v for k, v in fila.items()}

def obtener_filas():
    filas = sheet.get_all_records()
    return [normalizar_fila(f) for f in filas]

def guardar_o_actualizar(nombre, data):
    filas = obtener_filas()
    nombre_norm = normalizar_texto(nombre)

    fila_idx = None
    for i, f in enumerate(filas):
        if normalizar_texto(f.get("nombre_normalizado", "")) == nombre_norm:
            fila_idx = i + 2  # +2 por header
            break

    fila_data = [
        nombre,
        nombre_norm,
        data.get("hora_inicio", ""),
        data.get("hora_fin", ""),
        json.dumps(data.get("respuestas", {})),
        data.get("idx", 0),
        json.dumps(data.get("preguntas", []))
    ]

    if fila_idx:
        sheet.update(values=[fila_data], range_name=f"A{fila_idx}:G{fila_idx}")
    else:
        sheet.append_row(fila_data)

# =========================
# CARGAR PREGUNTAS
# =========================
with open("preguntas.json", "r", encoding="utf-8") as f:
    banco = json.load(f)

abiertas = [p for p in banco if p["tipo"] == "abierta"]
cerradas = [p for p in banco if p["tipo"] == "cerrada"]

preguntas = random.sample(abiertas, 6) + random.sample(cerradas, 4)
random.shuffle(preguntas)

# =========================
# SESSION STATE
# =========================
if "nombre" not in st.session_state:
    st.session_state.nombre = None
if "idx" not in st.session_state:
    st.session_state.idx = 0
if "respuestas" not in st.session_state:
    st.session_state.respuestas = {}
if "preguntas" not in st.session_state:
    st.session_state.preguntas = []
if "hora_inicio" not in st.session_state:
    st.session_state.hora_inicio = ""
if "hora_fin" not in st.session_state:
    st.session_state.hora_fin = ""

# =========================
# LOGIN
# =========================
if not st.session_state.nombre:
    st.title("Parcial")

    nombre = st.text_input("Ingrese su nombre completo")

    if st.button("Iniciar"):
        if nombre.strip() == "":
            st.warning("Debe ingresar su nombre")
        else:
            filas = obtener_filas()
            nombre_norm = normalizar_texto(nombre)

            existente = None
            for f in filas:
                if normalizar_texto(f.get("nombre_normalizado", "")) == nombre_norm:
                    existente = f
                    break

            if existente:
                st.session_state.nombre = nombre
                st.session_state.idx = int(existente.get("ultima_pregunta", 0))
                st.session_state.respuestas = json.loads(existente.get("respuestas_json", "{}")) if existente.get("respuestas_json") else {}
                st.session_state.preguntas = json.loads(existente.get("preguntas_json", "[]")) if existente.get("preguntas_json") else []
                st.session_state.hora_inicio = existente.get("hora_inicio", "")
                st.session_state.hora_fin = existente.get("hora_fin", "")
            else:
                st.session_state.nombre = nombre
                st.session_state.idx = 0
                st.session_state.respuestas = {}
                st.session_state.preguntas = preguntas
                st.session_state.hora_inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                guardar_o_actualizar(nombre, {
                    "hora_inicio": st.session_state.hora_inicio,
                    "hora_fin": "",
                    "respuestas": {},
                    "idx": 0,
                    "preguntas": st.session_state.preguntas
                })

            st.rerun()

    st.stop()

# =========================
# EXAMEN
# =========================
st.title("Parcial en curso")

idx = st.session_state.idx
preguntas = st.session_state.preguntas

if idx < len(preguntas):

    pregunta = preguntas[idx]

    st.write(f"Pregunta {idx+1}")
    st.write(pregunta["enunciado"])

    if pregunta["tipo"] == "cerrada":
        respuesta = st.radio(
            "Seleccione una opción",
            pregunta["opciones"],
            key=f"p{idx}"
        )
    else:
        respuesta = st.text_input(
            "Respuesta",
            key=f"p{idx}"
        )

    if st.button("Siguiente"):
        if not respuesta:
            st.warning("Debe responder antes de continuar")
        else:
            st.session_state.respuestas[str(idx)] = respuesta
            st.session_state.idx += 1

            guardar_o_actualizar(st.session_state.nombre, {
                "hora_inicio": st.session_state.hora_inicio,
                "hora_fin": "",
                "respuestas": st.session_state.respuestas,
                "idx": st.session_state.idx,
                "preguntas": st.session_state.preguntas
            })

            st.rerun()

else:
    if not st.session_state.hora_fin:
        st.session_state.hora_fin = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        guardar_o_actualizar(st.session_state.nombre, {
            "hora_inicio": st.session_state.hora_inicio,
            "hora_fin": st.session_state.hora_fin,
            "respuestas": st.session_state.respuestas,
            "idx": st.session_state.idx,
            "preguntas": st.session_state.preguntas
        })

    st.success("Ha finalizado el cuestionario")

    st.markdown("### Parte práctica")
    st.link_button("Ir al repositorio", "https://github.com/cuestamario-web/Parcial_ElectivaIII_D")

    with open("parcial2.docx", "rb") as f:
        st.download_button("Descargar guía", f, file_name="parcial2.docx")
