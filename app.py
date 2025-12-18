import streamlit as st
from google import genai
from google.genai import types
import os
import time

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Tutor Python IA", page_icon="🐍", layout="centered")

# --- 1. GESTIÓN DE LA API KEY ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("⚠️ No se ha encontrado la API Key. Configura 'GOOGLE_API_KEY'.")
    st.stop()

# Cache del cliente para estabilidad
@st.cache_resource
def get_client(api_key):
    return genai.Client(api_key=api_key)

client = get_client(api_key)

# ==========================================
# 🔍 BARRA LATERAL (SELECTOR DE MODELOS)
# ==========================================
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Lista de modelos robustos (usamos versiones específicas para evitar 404)
    mis_modelos = [
        "gemini-1.5-flash-002",  # Versión más estable actual
        "gemini-1.5-flash",      # Alias genérico
        "gemini-1.5-flash-8b",   # Versión ligera (menos saturación)
        "gemini-2.0-flash-exp"   # Experimental (Cuidado con los límites)
    ]
    
    selected_model = st.selectbox("Modelo:", mis_modelos, index=0)
    
    # Botón de pánico para limpiar memoria
    if st.button("🗑️ Reiniciar Chat", type="primary"):
        st.session_state.messages = []
        if "chat_session" in st.session_state:
            del st.session_state.chat_session
        st.rerun()

# ==========================================

# --- 2. CARGA DEL CONTEXTO ---
@st.cache_data 
def load_context():
    try:
        if os.path.exists('contexto.txt'):
            with open('contexto.txt', 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    except: return ""

context_text = load_context()

# --- 3. TU SYSTEM PROMPT (EXACTO) ---
SYSTEM_PROMPT = f"""
ROL:
Eres el "Tutor IA", un asistente docente experto en Python y pedagogía para alumnos de Secundaria/Bachillerato.
Tu objetivo NO es dar respuestas, sino enseñar a pensar.

BASE DE CONOCIMIENTO (CONTEXTO):
Toda tu enseñanza debe basarse EXCLUSIVAMENTE en el siguiente texto. Si el alumno pregunta algo que no está aquí, asume que aún no lo han estudiado.
--------------------------------------------------
{context_text}
--------------------------------------------------

INSTRUCCIONES PARA EL USO DE IMÁGENES:
Si en el CONTEXTO anterior aparecen URLs de imágenes asociadas a un tema, ¡ÚSALAS!
Cuando expliques ese tema, inserta la imagen usando formato Markdown exacto:
![Descripción breve](URL_DE_LA_IMAGEN)
(Hazlo de forma natural, como: "Fíjate en este esquema:")

TU ALGORITMO DE RESPUESTA (MÉTODO SOCRÁTICO GUIADO):
Cuando el alumno te haga una pregunta o te muestre código, sigue estos pasos mentalmente:

1. ANÁLISIS: ¿Qué intenta hacer el alumno? ¿Qué concepto del CONTEXTO necesita usar?
2. DIAGNÓSTICO: ¿Dónde está su error o confusión?
3. ESTRATEGIA: No le des la solución. Divide el problema en el paso más pequeño posible.
4. ACCIÓN:
   - Si el código tiene error: No lo corrijas. Pregúntale sobre la línea específica. (Ej: "¿Qué valor crees que tiene la variable 'x' en la línea 3?")
   - Si pregunta "¿Cómo se hace X?": Pídele que revise una parte concreta de los apuntes o dale una pista de sintaxis incompleta.
   - Si está bloqueado: Dale un ejemplo parecida (análogo) pero con otros datos, para que él deduzca la regla.

REGLAS DE ORO (MANDAMIENTOS):
- JAMÁS escribas el código completo de la solución. NUNCA.
- Si te piden "Hazme el ejercicio", responde: "Me dice Gonzalo que su venganza sería terrible si te lo hiciera yo. Yo soy tu copiloto, no el piloto. Escribe tú cómo empezarías y yo te corrijo".
- Sé paciente, amable y usa emojis ocasionalmente (🐍, 💻, 💡).
- Si el concepto implica una imagen del contexto, muéstrala.
- PREGUNTAS GUÍA: Termina tus intervenciones con una pregunta sencilla que les obligue a deducir el siguiente paso.

EJEMPLOS DE INTERACCIÓN DESEADA:

Alumno: "No me funciona el bucle."
Tutor (MAL): "Te falta poner dos puntos al final de la línea while."
Tutor (BIEN): "¡Casi lo tienes! Mira bien la línea del 'while'. En Python, ¿qué signo de puntuación necesitamos poner siempre al final de una instrucción de bloque (como if o for) para decir 'aquí empieza lo de dentro'? 🧐"

Alumno: "¿Cómo sumo dos variables?"
Tutor (BIEN): "Para sumar usamos un operador matemático, igual que en clase de mates. Si tienes 'a' y 'b', ¿cómo lo escribirías en papel? Intenta escribir el código tú mismo aquí."
"""

# --- 4. GESTIÓN DE LA SESIÓN ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Detectar cambio de modelo y reiniciar si es necesario
if "current_model" not in st.session_state:
    st.session_state.current_model = selected_model

if st.session_state.current_model != selected_model:
    st.session_state.current_model = selected_model
    if "chat_session" in st.session_state:
        del st.session_state.chat_session 

# Crear Chat con el prompt
if "chat_session" not in st.session_state:
    try:
        st.session_state.chat_session = client.chats.create(
            model=selected_model, 
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.7 # Creatividad controlada
            )
        )
    except Exception as e:
        st.error(f"Error al iniciar con {selected_model}: {e}")

# --- 5. INTERFAZ GRÁFICA ---
st.title("🐍 Tutor de Python")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. INTERACCIÓN (CON REINTENTOS) ---
if prompt := st.chat_input("Escribe tu duda..."):
    # Guardar usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Intentar responder (Manejo de errores 429 y 404)
    try:
        with st.spinner(f"Pensando con {selected_model}..."):
            response = st.session_state.chat_session.send_message(prompt)
            bot_reply = response.text
            
    except Exception as e:
        # Si falla por saturación o límites
        if "429" in str(e) or "RESOURCE" in str(e):
            with st.chat_message("assistant"):
                st.warning("🚦 IA saturada. Reintentando en 3 seg...")
                time.sleep(3)
                try:
                    response = st.session_state.chat_session.send_message(prompt)
                    bot_reply = response.text
                except:
                    st.error("❌ La IA está muy ocupada o has gastado tu cuota diaria. Prueba a cambiar el modelo en la izquierda.")
                    st.stop()
        else:
            st.error(f"Error técnico: {e}")
            st.stop()

    # Mostrar respuesta
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
