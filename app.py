import streamlit as st
import json
import time
import random
import re
import gspread
from google.oauth2.service_account import Credentials

# =====================
# NORMALIZAR NOMBRE
# =====================
def normalizar_nombre(nombre):
    nombre = nombre.strip().lower()
    nombre = re.sub(r"\s+", " ", nombre)
    return nombre

# =====================
# GOOGLE SHEETS
# =====================
def conectar_sheets():
    creds = Credentials.from_service_account_info(
        json.loads(st.secrets["gcp_service_account"]["json"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    return client.open("respuestas_parcial").sheet1

def buscar_estudiante(sheet, nombre_norm):
    data = sheet.get_all_records()
    for i, row in enumerate(data, start=2):
        if row["nombre_normalizado"] == nombre_norm:
            return i, row
    return None, None

def guardar_o_actualizar(data):
    sheet = conectar_sheets()
    fila, existente = buscar_estudiante(sheet, data["nombre_norm"])

    fila_data = [
        data["nombre"],
        data["nombre_norm"],
        data["hora_inicio"],
        data["hora_fin"],
        json.dumps(data["respuestas"]),
        data["idx"],
        json.dumps(data["preguntas"])
    ]

    if fila:
        sheet.update(f"A{fila}:G{fila}", [fila_data])
    else:
        sheet.append_row(fila_data)

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
# LOGIN / CONTROL INTENTO
# =====================
if "nombre" not in st.session_state:
    nombre = st.text_input("Nombre completo")

    if st.button("Iniciar / Continuar"):
        if nombre.strip():
            nombre_norm = normalizar_nombre(nombre)
            sheet = conectar_sheets()
            fila, existente = buscar_estudiante(sheet, nombre_norm)

            if existente:
                # 🔒 SI YA TERMINÓ → BLOQUEAR
                if existente["hora_fin"]:
                    st.error("Ya existe un intento finalizado para este estudiante")
                    st.stop()

                # 🔁 RECUPERAR
                st.session_state.nombre = existente["nombre"]
                st.session_state.nombre_norm = nombre_norm
                st.session_state.hora_inicio = existente["hora_inicio"]
                st.session_state.respuestas = json.loads(existente["respuestas_json"]) if existente["respuestas_json"] else {}
                st.session_state.idx = int(existente["ultima_pregunta"])
                st.session_state.preguntas = json.loads(existente["preguntas_json"])
                st.session_state.hora_fin = existente["hora_fin"]

            else:
                # 🆕 NUEVO
                preguntas = seleccionar_preguntas()

                st.session_state.nombre = nombre
                st.session_state.nombre_norm = nombre_norm
                st.session_state.hora_inicio = time.strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.idx = 0
                st.session_state.respuestas = {}
                st.session_state.preguntas = preguntas
                st.session_state.hora_fin = None

                guardar_o_actualizar({
                    "nombre": nombre,
                    "nombre_norm": nombre_norm,
                    "hora_inicio": st.session_state.hora_inicio,
                    "hora_fin": None,
                    "respuestas": {},
                    "idx": 0,
                    "preguntas": preguntas
                })

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

            guardar_o_actualizar({
                "nombre": st.session_state.nombre,
                "nombre_norm": st.session_state.nombre_norm,
                "hora_inicio": st.session_state.hora_inicio,
                "hora_fin": st.session_state.hora_fin,
                "respuestas": st.session_state.respuestas,
                "idx": st.session_state.idx,
                "preguntas": st.session_state.preguntas
            })

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
        guardar_o_actualizar({
            "nombre": st.session_state.nombre,
            "nombre_norm": st.session_state.nombre_norm,
            "hora_inicio": st.session_state.hora_inicio,
            "hora_fin": st.session_state.hora_fin,
            "respuestas": st.session_state.respuestas,
            "idx": st.session_state.idx,
            "preguntas": st.session_state.preguntas
        })

        st.success("Examen finalizado correctamente")
        st.session_state.clear()
