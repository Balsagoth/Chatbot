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
# --- 3. DEFINICIÓN DE LA PERSONALIDAD (CEREBRO DEL PROFESOR) ---
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
- Si te piden "Hazme el ejercicio", responde: "Yo soy tu copiloto, no el piloto. Escribe tú cómo empezarías y yo te corrijo".
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


