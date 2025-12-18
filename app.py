import streamlit as st
from google import genai
from google.genai import types # Necesario para pasar las instrucciones del sistema en la nueva versión
import os

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Tutor Python IA",
    page_icon="🐍",
    layout="centered"
)

# --- 1. GESTIÓN DE LA API KEY ---
# Intentamos obtener la clave de los 'secrets' de Streamlit o variable de entorno
try:
    # Usamos un nombre estándar. Asegúrate de que en tus secrets se llame GOOGLE_API_KEY
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    # Si falla, miramos en variables de entorno (para local)
    api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("⚠️ No se ha encontrado la API Key. Configura 'GOOGLE_API_KEY' en los secrets de Streamlit.")
    st.stop()

# Configuración nueva (Cliente Oficial 2025)
client = genai.Client(api_key=api_key)

# --- 2. CARGA DEL CONTEXTO (TUS APUNTES) ---
@st.cache_data 
def load_context():
    try:
        # Intenta leer el archivo si existe
        if os.path.exists('contexto.txt'):
            with open('contexto.txt', 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    except Exception:
        return ""

context_text = load_context()

# --- 3. DEFINICIÓN DE LA PERSONALIDAD (SYSTEM INSTRUCTION) ---
SYSTEM_PROMPT = f"""
Eres un TUTOR SOCRÁTICO experto en Python y pedagogía.
Tu misión es ayudar al alumno a entender, NO hacerle el trabajo.

CONTEXTO DE LA ASIGNATURA (BÁSATE EN ESTO):
{context_text}

TUS REGLAS OBLIGATORIAS:
1.  PROHIBIDO DAR CÓDIGO FINAL: Si el alumno pide un ejercicio, nunca escribas la solución completa.
2.  MÉTODO SOCRÁTICO: Responde siempre con una pregunta guía o una pista pequeña.
3.  GESTIÓN DE ERRORES: Si el alumno te pega un código con error, no lo corrijas. Dile: "Fíjate en la línea X, ¿qué crees que pasa con la variable Y?".
4.  RECHAZA TEMAS AJENOS: Si te preguntan de Historia o Lengua, di cortésmente que solo eres profesor de Python.
5.  TONO: Sé animado, motivador, pero firme. Usa emojis ocasionalmente 🐍.

Si el alumno dice "hazme el código", tu respuesta debe ser:
"No puedo escribir el código por ti, eso no te ayudaría a aprender. Pero dime, ¿cómo plantearías el primer paso?"
"""

# --- 4. GESTIÓN DE LA SESIÓN (HISTORIAL) ---
# Inicializamos el historial visual para Streamlit
if "messages" not in st.session_state:
    st.session_state.messages = []

# Configuramos la sesión del chat de Gemini (LÓGICA NUEVA)
if "chat_session" not in st.session_state:
    # En la nueva SDK, se crea el chat a través del cliente
    st.session_state.chat_session = client.chats.create(
        model="gemini-1.5-flash", 
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.7 # Creatividad controlada para un profesor
        )
    )

# --- 5. INTERFAZ GRÁFICA (FRONTEND) ---
st.title("🐍 Tutor de Python")
st.markdown("""
Bienvenido. Soy tu asistente personal de programación.
**No haré tus deberes**, pero te ayudaré a desbloquearte. ¡Pregunta!
""")

# Mostrar mensajes anteriores del historial visual
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. LÓGICA DE INTERACCIÓN ---
if prompt := st.chat_input("Escribe tu duda o pega tu código aquí..."):
    
    # A) Mostrar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # B) Generar respuesta con Gemini
    try:
        with st.spinner("Analizando tu código..."):
            # Enviar mensaje a la sesión de Gemini
            # Nota: En la nueva SDK el método sigue siendo send_message
            response = st.session_state.chat_session.send_message(prompt)
            bot_reply = response.text
            
        # C) Mostrar respuesta del bot
        with st.chat_message("assistant"):
            st.markdown(bot_reply)
            
        # D) Guardar en historial visual
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        
    except Exception as e:
        st.error(f"Hubo un error de conexión: {e}")
