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

# 1) Pedir nombre
name = st.text_input("¿Cuál es tu nombre?")
if not name:
    st.stop()

# 2) Selección Sí/No con placeholder
secuencia = ["", "Sí", "No"]
desea = st.radio(
    "¿Quieres hacer un test de cultura general?",
    secuencia,
    key="desea"
)
if desea == "":
    st.write("👉 Por favor selecciona “Sí” o “No” para continuar.")
    st.stop()
elif desea == "No":
    st.info("Está bien, ¡tal vez otro día! 😄")
    st.stop()

# 3) Inicializar quiz en sesión
if "preguntas" not in st.session_state:
    response = requests.get("https://the-trivia-api.com/api/questions?limit=5")
    data = response.json()
    preguntas = []
    for q in data:
        texto = GoogleTranslator(source='auto', target='es').translate(q['question'])
        correcta = GoogleTranslator(source='auto', target='es').translate(q['correctAnswer'])
        incorrectas = [GoogleTranslator(source='auto', target='es').translate(x) for x in q['incorrectAnswers']]
        opciones = incorrectas + [correcta]
        random.shuffle(opciones)
        preguntas.append({"pregunta": texto, "correcta": correcta, "opciones": opciones})
    st.session_state.preguntas = preguntas
    st.session_state.index = 0
    st.session_state.correctas = 0
    st.session_state.ultima = None

# 4) Mostrar una pregunta a la vez
total = len(st.session_state.preguntas)
idx = st.session_state.index
if idx < total:
    actual = st.session_state.preguntas[idx]
    st.subheader(f"Pregunta {idx+1} de {total}")
    respuesta = st.radio(
        actual["pregunta"],
        actual["opciones"],
        key=f"respuesta_{idx}"
    )

    # Placeholder para alternar botón
    btn = st.empty()
    if st.session_state.ultima is None:
        if btn.button("Responder"):
            if respuesta == actual["correcta"]:
                st.success("✅ ¡Correcto!")
                st.session_state.correctas += 1
            else:
                st.error(f"❌ Incorrecto. Era: {actual['correcta']}")
            st.session_state.ultima = True
    else:
        if btn.button("Siguiente"):
            st.session_state.index += 1
            st.session_state.ultima = None

# 5) Resultado final
else:
    st.markdown("## 🎯 Resultado final")
    aciertos = st.session_state.correctas
    if aciertos > total/2:
        st.success(f"🎉 {name}, acertaste {aciertos}/{total}. ¡Buen trabajo!")
    else:
        st.error(f"❌ {name}, solo acertaste {aciertos}/{total}. ¡Sigue practicando!")
    if st.button("Reiniciar quiz"):
        for k in ["preguntas", "index", "correctas", "ultima", "desea"]:
            st.session_state.pop(k, None)
        st.experimental_rerun()

