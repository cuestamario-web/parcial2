import streamlit as st
import json
import time
import os

# =====================
# CONFIGURACIÓN
# =====================
st.set_page_config(page_title="Sistema de Parciales", layout="wide")

DATA_FILE = "preguntas.json"
RESP_FILE = "respuestas.json"
TIEMPO_EXAMEN = 60 * 30  # 30 minutos
DOCENTE_PASSWORD = "admin123"  # 🔐 Cambia esto

# =====================
# UTILIDADES
# =====================

def cargar_preguntas():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def guardar_preguntas(preguntas):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(preguntas, f, indent=4, ensure_ascii=False)


def guardar_respuesta(data):
    if os.path.exists(RESP_FILE):
        with open(RESP_FILE, "r", encoding="utf-8") as f:
            respuestas = json.load(f)
    else:
        respuestas = []

    respuestas.append(data)

    with open(RESP_FILE, "w", encoding="utf-8") as f:
        json.dump(respuestas, f, indent=4, ensure_ascii=False)

# =====================
# LOGIN DOCENTE
# =====================

def login_docente():
    st.title("Acceso Docente")
    password = st.text_input("Ingrese contraseña", type="password")

    if st.button("Ingresar"):
        if password == DOCENTE_PASSWORD:
            st.session_state.auth_docente = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta")

# =====================
# MÓDULO DOCENTE
# =====================

def modulo_docente():
    if "auth_docente" not in st.session_state:
        login_docente()
        return

    st.title("Módulo Docente - Banco de Preguntas")

    preguntas = cargar_preguntas()

    with st.form("form_pregunta"):
        tipo = st.selectbox("Tipo de pregunta", ["multiple", "abierta"])
        enunciado = st.text_area("Enunciado")

        opciones = []
        if tipo == "multiple":
            opciones = [
                st.text_input(f"Opción {i+1}") for i in range(4)
            ]

        seccion = st.selectbox("Sección", ["teoria", "practico"])

        submitted = st.form_submit_button("Guardar pregunta")

        if submitted:
            pregunta = {
                "tipo": tipo,
                "enunciado": enunciado,
                "opciones": opciones,
                "seccion": seccion
            }
            preguntas.append(pregunta)
            guardar_preguntas(preguntas)
            st.success("Pregunta guardada")

    st.subheader("Preguntas existentes")
    for i, p in enumerate(preguntas):
        st.write(f"{i+1}. {p['enunciado']} ({p['tipo']})")

# =====================
# MÓDULO ESTUDIANTE
# =====================

def modulo_estudiante():
    st.title("Parcial")

    if "nombre" not in st.session_state:
        nombre = st.text_input("Ingrese su nombre completo")
        if st.button("Iniciar examen"):
            if nombre.strip() != "":
                st.session_state.nombre = nombre
                st.session_state.start_time = time.time()
                st.session_state.pagina = 0
                st.session_state.respuestas = {}
                st.rerun()
            else:
                st.warning("Debe ingresar su nombre")
        return

    preguntas = cargar_preguntas()
    preguntas = sorted(preguntas, key=lambda x: x["seccion"])

    tiempo_restante = TIEMPO_EXAMEN - (time.time() - st.session_state.start_time)

    if tiempo_restante <= 0:
        st.warning("Tiempo finalizado. Enviando intento...")
        finalizar_examen()
        return

    mins, secs = divmod(int(tiempo_restante), 60)
    st.info(f"Tiempo restante: {mins:02d}:{secs:02d}")

    idx = st.session_state.pagina

    if idx < len(preguntas):
        p = preguntas[idx]
        st.subheader(f"Pregunta {idx+1}")
        st.write(p["enunciado"])

        if p["tipo"] == "multiple":
            resp = st.radio("Seleccione una opción", p["opciones"], key=idx)
        else:
            resp = st.text_area("Respuesta", key=idx)

        if st.button("Siguiente"):
            st.session_state.respuestas[idx] = resp
            st.session_state.pagina += 1
            st.rerun()
    else:
        finalizar_examen()


def finalizar_examen():
    data = {
        "nombre": st.session_state.nombre,
        "respuestas": st.session_state.respuestas,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    guardar_respuesta(data)

    st.success("Examen finalizado y guardado")
    st.session_state.clear()

# =====================
# MAIN
# =====================

modo = st.sidebar.selectbox("Modo", ["Estudiante", "Docente"])

if modo == "Docente":
    modulo_docente()
else:
    modulo_estudiante()
