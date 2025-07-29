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

# Inicializar estado si no existe
if "preguntas" not in st.session_state:
    st.session_state.preguntas = []
    st.session_state.index = 0
    st.session_state.correctas = 0
    st.session_state.quiz_iniciado = False

# Botón para empezar el quiz
if name and not st.session_state.quiz_iniciado:
    if st.button("¡Sí, quiero hacer el test!"):
        # Cargar preguntas solo una vez
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
        st.session_state.quiz_iniciado = True

# Mostrar una pregunta a la vez
if st.session_state.quiz_iniciado and st.session_state.index < len(st.session_state.preguntas):
    actual = st.session_state.preguntas[st.session_state.index]
    st.subheader(f"Pregunta {st.session_state.index + 1}")
    respuesta = st.radio(actual["pregunta"], actual["opciones"], key=st.session_state.index)

    if st.button("Responder"):
        if respuesta == actual["correcta"]:
            st.success("¡Correcto!")
            st.session_state.correctas += 1
        else:
            st.error(f"Incorrecto. La respuesta correcta era: {actual['correcta']}")
        st.session_state.index += 1

# Resultado final
if st.session_state.index == len(st.session_state.preguntas) and st.session_state.quiz_iniciado:
    st.markdown("## Resultado final:")
    if st.session_state.correctas > 3:
        st.success(f"🎉 ¡Felicidades {name}! Aprobaste con {st.session_state.correctas}/5 respuestas correctas.")
    else:
        st.error(f"❌ Lo siento {name}, obtuviste {st.session_state.correctas}/5. ¡Puedes intentarlo de nuevo!")

    # Botón para reiniciar
    if st.button("Reiniciar quiz"):
        st.session_state.preguntas = []
        st.session_state.index = 0
        st.session_state.correctas = 0
        st.session_state.quiz_iniciado = False
