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

def buscar_estudiante(sheet, nombre):
    data = sheet.get_all_records()
    for i, row in enumerate(data, start=2):
        if row["nombre"] == nombre:
            return i, row
    return None, None

def guardar_o_actualizar(data):
    sheet = conectar_sheets()
    fila, existente = buscar_estudiante(sheet, data["nombre"])

    if fila:
        sheet.update(f"A{fila}:E{fila}", [[
            data["nombre"],
            data["hora_inicio"],
            data["hora_fin"],
            json.dumps(data["respuestas"]),
            data["idx"]
        ]])
    else:
        sheet.append_row([
            data["nombre"],
            data["hora_inicio"],
            data["hora_fin"],
            json.dumps(data["respuestas"]),
            data["idx"]
        ])

# =====================
# PREGUNTAS
# =====================
def cargar_preguntas():
    with open("preguntas.json", "r", encoding="utf-8") as f:
        return json.load(f)

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
# LOGIN / RECUPERACIÓN
# =====================
if "nombre" not in st.session_state:
    nombre = st.text_input("Nombre completo")

    if st.button("Iniciar / Continuar"):
        if nombre.strip():
            sheet = conectar_sheets()
            fila, existente = buscar_estudiante(sheet, nombre)

            if existente:
                # 🔥 RECUPERAR INTENTO
                st.session_state.nombre = nombre
                st.session_state.hora_inicio = existente["hora_inicio"]
                st.session_state.respuestas = json.loads(existente["respuestas_json"]) if existente["respuestas_json"] else {}
                st.session_state.idx = int(existente["ultima_pregunta"])
                st.session_state.preguntas = seleccionar_preguntas()

            else:
                # 🔥 NUEVO INTENTO
                st.session_state.nombre = nombre
                st.session_state.hora_inicio = time.strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.idx = 0
                st.session_state.respuestas = {}
                st.session_state.preguntas = seleccionar_preguntas()
                st.session_state.hora_fin = None

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

            if i == len(preguntas) - 1:
                st.session_state.hora_fin = time.strftime("%Y-%m-%d %H:%M:%S")

            st.session_state.pop(key_actual, None)
            st.session_state.idx += 1

            # 🔥 GUARDADO AUTOMÁTICO
            data = {
                "nombre": st.session_state.nombre,
                "hora_inicio": st.session_state.hora_inicio,
                "hora_fin": st.session_state.hora_fin,
                "respuestas": st.session_state.respuestas,
                "idx": st.session_state.idx
            }

            guardar_o_actualizar(data)

            st.rerun()

# =====================
# FINAL
# =====================
else:
    st.success("Has terminado la parte teórica")

    st.markdown("## Parte práctica")

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
            "hora_fin": st.session_state.hora_fin,
            "respuestas": st.session_state.respuestas,
            "idx": st.session_state.idx
        }

        guardar_o_actualizar(data)

        st.success("Examen finalizado correctamente")
        st.session_state.clear()
