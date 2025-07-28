import unicodedata
import requests
from deep_translator import GoogleTranslator
import random
import streamlit as st

def normalizar(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto.lower())
        if unicodedata.category(c) != 'Mn'
    )

st.title("🎓 Test de Cultura General")

# Paso 1: Nombre del usuario
name = st.text_input("¿Cuál es tu nombre?")

# Paso 2: Confirmar si desea hacer el test
if name:
    st.write(f"Hola, {name} 👋 ¿quieres hacer un test de cultura general?")
    if st.button("¡Sí, quiero hacerlo!"):
        respuestas_correctas = 0
        response = requests.get("https://the-trivia-api.com/api/questions?limit=5")
        data = response.json()

        for i, pregunta in enumerate(data, 1):
            pregunta_es = GoogleTranslator(source='auto', target='es').translate(pregunta['question'])
            correct_es = GoogleTranslator(source='auto', target='es').translate(pregunta['correctAnswer'])
            incorrectas_es = [GoogleTranslator(source='auto', target='es').translate(ans) for ans in pregunta['incorrectAnswers']]
            opciones = incorrectas_es + [correct_es]
            random.shuffle(opciones)

            respuesta = st.radio(f"{i}. {pregunta_es}", opciones, key=f"pregunta_{i}")
            if respuesta == correct_es:
                respuestas_correctas += 1

        st.markdown("## Resultado del Test:")
        if respuestas_correctas > 3:
            st.success(f"🎉 ¡Felicidades {name}! Has pasado el test con {respuestas_correctas}/5 respuestas correctas.")
        else:
            st.error(f"❌ Lo siento {name}, solo acertaste {respuestas_correctas}/5. ¡Inténtalo de nuevo!")