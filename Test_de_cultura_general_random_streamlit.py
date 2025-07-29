import unicodedata
import requests
from deep_translator import GoogleTranslator
import random
import streamlit as st

# Función para normalizar texto
def normalizar(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto.lower())
        if unicodedata.category(c) != 'Mn'
    )

st.title("🎓 Test de Cultura General")

# Paso 1: Nombre del usuario
name = st.text_input("¿Cuál es tu nombre?")

# Inicializar estados
if "estado" not in st.session_state:
    st.session_state.estado = "esperando_nombre"  # puede ser: esperando_nombre, confirmar, quiz, resultado
    st.session_state.preguntas = []
    st.session_state.index = 0
    st.session_state.correctas = 0
    st.session_state.ultima_respuesta_correcta = None

# Paso 2: Confirmación para hacer el test
if name and st.session_state.estado == "esperando_nombre":
    st.session_state.estado = "confirmar"

if st.session_state.estado == "confirmar":
    st.subheader(f"Hola {name} 👋")
    desea = st.radio("¿Quieres hacer un test de cultura general?", ["Sí", "No"])
    if desea == "Sí":
        st.session_state.estado = "quiz"
        # Cargar preguntas
        response = requests.get("https://the-trivia-api.com/api/questions?limit=5")
        data = response.json()
        preguntas = []
        for pregunta in data:
            pregunta_es = GoogleTranslator(source='auto', target='es').translate(pregunta['question'])
            correct_es = GoogleTranslator(source='auto', target='es').translate(pregunta['correctAnswer'])
            incorrectas_es = [GoogleTranslator(source='auto', target='es').translate(ans) for ans in pregunta['incorrectAnswers']]
            opciones = incorrectas_es + [correct_es]
            random.shuffle(opciones)
            preguntas.append({
                "pregunta": pregunta_es,
                "correcta": correct_es,
                "opciones": opciones
            })
        st.session_state.preguntas = preguntas
    elif desea == "No":
        st.info("Está bien, ¡tal vez otro día! 😄")
        st.stop()

# Paso 3: Mostrar preguntas una a una
if st.session_state.estado == "quiz" and st.session_state.index < len(st.session_state.preguntas):
    actual = st.session_state.preguntas[st.session_state.index]
    st.subheader(f"Pregunta {st.session_state.index + 1}")
    respuesta = st.radio(actual["pregunta"], actual["opciones"], key=st.session_state.index)

    if st.button("Responder"):
        if respuesta == actual["correcta"]:
            st.success("✅ ¡Correcto!")
            st.session_state.correctas += 1
            st.session_state.ultima_respuesta_correcta = True
        else:
            st.error(f"❌ Incorrecto. La respuesta correcta era: {actual['correcta']}")
            st.session_state.ultima_respuesta_correcta = False

    if st.session_state.ultima_respuesta_correcta is not None:
        if st.button("Siguiente"):
            st.session_state.index += 1
            st.session_state.ultima_respuesta_correcta = None

# Paso 4: Resultado final
if st.session_state.index == len(st.session_state.preguntas) and st.session_state.estado == "quiz":
    st.session_state.estado = "resultado"
    st.markdown("## 🎯 Resultado final:")
    if st.session_state.correctas > 3:
        st.success(f"🎉 ¡Felicidades {name}! Aprobaste con {st.session_state.correctas}/5 respuestas correctas.")
    else:
        st.error(f"❌ Lo siento {name}, obtuviste {st.session_state.correctas}/5. ¡Puedes intentarlo de nuevo!")

    if st.button("Reiniciar test"):
        st.session_state.estado = "confirmar"
        st.session_state.index = 0
        st.session_state.correctas = 0
        st.session_state.preguntas = []
        st.session_state.ultima_respuesta_correcta = None

