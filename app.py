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
# --- AQUÍ ESTÁ EL TRUCO: CACHE_RESOURCE ---
# Usamos este decorador para que el cliente NO se cierre al recargar la página
@st.cache_resource
def get_client(api_key):
    return genai.Client(api_key=api_key)

# En lugar de crear el cliente directamente, llamamos a la función cacheada
client = get_client(api_key)


# ==========================================
@@ -160,24 +161,25 @@
            with st.chat_message("assistant"):
                st.warning("🚦 Google está saturado. Esperando 5 segundos para reintentar...")
                time.sleep(5) # Esperamos 5 segundos
                try:
                    # INTENTO 2: Reintentamos automáticamente
                    response = st.session_state.chat_session.send_message(prompt)
                    bot_reply = response.text
                except Exception as e2:
                    st.error("❌ Imposible conectar tras reintentar. Prueba en 1 minuto.")
                    st.stop() # Paramos aquí
        else:
            # Si es otro error (como que se cayó internet), avisamos
            st.error(f"Error de conexión: {e}")
            if "client has been closed" in str(e).lower():
                st.warning("⚠️ Recarga la página (F5).")
            st.stop()

    # C) Si todo ha ido bien (en el intento 1 o 2), mostramos la respuesta
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})







