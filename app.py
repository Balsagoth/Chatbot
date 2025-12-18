import streamlit as st
from google import genai
from google.genai import types
import os

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

# Cliente Oficial
client = genai.Client(api_key=api_key)

# ==========================================
# 🔍 ZONA DE DIAGNÓSTICO (SOLO PARA EL PROFE)
# ==========================================
with st.sidebar:
    st.header("🔧 Diagnóstico de Modelos")
    st.write("Si da error 404, prueba con uno de estos nombres:")
    
    try:
        # Pedimos a Google la lista de modelos disponibles HOY
        # Iteramos sobre los modelos y filtramos los que generan contenido
        models = client.models.list() 
        valid_models = []
        for m in models:
            # Buscamos modelos que sirvan para 'generateContent'
            # Nota: la estructura del objeto puede variar, imprimimos el nombre directo
            name = m.name.split("/")[-1] # Quitamos el "models/" del principio
            if "gemini" in name and "vision" not in name: # Filtro básico
                valid_models.append(name)
        
        # Mostramos la lista para que puedas copiar
        selected_model = st.selectbox("Modelos detectados:", valid_models, index=0 if valid_models else None)
        st.caption(f"Usando ahora: `{selected_model}`")
        
    except Exception as e:
        st.error(f"No se pudo listar modelos: {e}")
        selected_model = "gemini-1.5-flash" # Fallback por defecto

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

# --- 3. DEFINICIÓN DE LA PERSONALIDAD ---
SYSTEM_PROMPT = f"""
TUS REGLAS OBLIGATORIAS:
1.  **PROHIBIDO DAR CÓDIGO FINAL:** Si el alumno pide un ejercicio, nunca escribas la solución completa.
2.  **MÉTODO SOCRÁTICO:** Responde siempre con una pregunta guía o una pista pequeña.
3.  **GESTIÓN DE ERRORES:** Si el alumno te pega un código con error, no lo corrijas. Dile: "Fíjate en la línea X, ¿qué crees que pasa con la variable Y?".
4.  **RECHAZA TEMAS AJENOS:** Si te preguntan de Historia o Lengua, di cortésmente que solo eres profesor de Python.
5.  **TONO:** Sé animado, motivador, pero firme. Usa emojis ocasionalmente 🐍.
"""

# --- 4. GESTIÓN DE LA SESIÓN ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Configuración del chat usando el modelo seleccionado en la barra lateral
if "chat_session" not in st.session_state or st.session_state.current_model != selected_model:
    st.session_state.current_model = selected_model
    try:
        st.session_state.chat_session = client.chats.create(
            model=selected_model, 
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.7
            )
        )
    except Exception as e:
        st.error(f"Error al iniciar chat con {selected_model}: {e}")

# --- 5. INTERFAZ GRÁFICA ---
st.title("🐍 Tutor de Python")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 6. INTERACCIÓN ---
if prompt := st.chat_input("Escribe tu duda..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.spinner(f"Pensando con {selected_model}..."):
            response = st.session_state.chat_session.send_message(prompt)
            bot_reply = response.text
            
        with st.chat_message("assistant"):
            st.markdown(bot_reply)
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
        
    except Exception as e:
        st.error(f"Error de conexión (Intenta cambiar el modelo en la barra izquierda): {e}")
