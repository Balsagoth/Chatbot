import streamlit as st
import google.generativeai as genai
import os

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Tutor Python IA",
    page_icon="🐍",
    layout="centered"
)

# --- 1. GESTIÓN DE LA API KEY ---
# Intentamos obtener la clave de los 'secrets' de Streamlit (para producción)
# o de una variable de entorno (para local).
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    # Si no estás en la nube de Streamlit, busca una variable de entorno
    # OJO: Nunca escribas la clave directamente en el código si vas a compartirlo.
    api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("⚠️ No se ha encontrado la API Key. Configura 'GEMINI_API_KEY' en los secrets.")
    st.stop()

genai.configure(api_key=api_key)

# --- 2. CARGA DEL CONTEXTO (TUS APUNTES) ---
@st.cache_data # Esto hace que no se recargue el archivo cada vez que alguien escribe
def load_context():
    try:
        with open('contexto.txt', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        st.warning("⚠️ No se encontró el archivo 'contexto.txt'. La IA no tendrá tus apuntes.")
        return ""

context_text = load_context()

# --- 3. DEFINICIÓN DE LA PERSONALIDAD (SYSTEM INSTRUCTION) ---
# Aquí es donde ocurre la magia para evitar que copien.
SYSTEM_PROMPT = f"""
Eres un TUTOR SOCRÁTICO experto en Python y pedagogía.
Tu misión es ayudar al alumno a entender, NO hacerle el trabajo.

CONTEXTO DE LA ASIGNATURA (BÁSATE EN ESTO):
{context_text}

TUS REGLAS OBLIGATORIAS:
1.  **PROHIBIDO DAR CÓDIGO FINAL:** Si el alumno pide un ejercicio, nunca escribas la solución completa.
2.  **MÉTODO SOCRÁTICO:** Responde siempre con una pregunta guía o una pista pequeña.
3.  **GESTIÓN DE ERRORES:** Si el alumno te pega un código con error, no lo corrijas. Dile: "Fíjate en la línea X, ¿qué crees que pasa con la variable Y?".
4.  **RECHAZA TEMAS AJENOS:** Si te preguntan de Historia o Lengua, di cortésmente que solo eres profesor de Python.
5.  **TONO:** Sé animado, motivador, pero firme. Usa emojis ocasionalmente 🐍.

Si el alumno dice "hazme el código", tu respuesta debe ser:
"No puedo escribir el código por ti, eso no te ayudaría a aprender. Pero dime, ¿cómo plantearías el primer paso?"
"""

# --- 4. GESTIÓN DE LA SESIÓN (HISTORIAL) ---
# Inicializamos el historial de chat si no existe
if "messages" not in st.session_state:
    st.session_state.messages = []

# Configuramos el modelo de Gemini
if "chat_session" not in st.session_state:
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash", # Modelo rápido y eficiente
        system_instruction=SYSTEM_PROMPT
    )
    st.session_state.chat_session = model.start_chat(history=[])

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
# Capturar input del usuario
if prompt := st.chat_input("Escribe tu duda o pega tu código aquí..."):
    
    # 1. Mostrar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generar respuesta con Gemini
    try:
        with st.spinner("Analizando tu código..."):
            # Enviamos el mensaje a la sesión de Gemini guardada
            response = st.session_state.chat_session.send_message(prompt)
            bot_reply = response.text
            
        # 3. Mostrar respuesta del bot
        with st.chat_message("assistant"):
            st.markdown(bot_reply)
            
        # 4. Guardar en historial visual
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        
    except Exception as e:
        st.error(f"Hubo un error de conexión: {e}")



