import unicodedata
import requests
from deep_translator import GoogleTranslator
import random
import streamlit as st

# Configuración de la página\ nst.set_page_config(page_title="Test de Cultura General", page_icon="🎓")

# Función para normalizar texto (opcional)
def normalizar(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto.lower())
        if unicodedata.category(c) != 'Mn'
    )

# Título de la app
st.title("🎓 Test de Cultura General")

# 1) Pedir nombre
name = st.text_input("¿Cuál es tu nombre?")
if not name:
    st.stop()

# 2) Precarga y traducción de preguntas (solo una vez)
if "preguntas" not in st.session_state:
    with st.spinner("Cargando y traduciendo preguntas..."):
        response = requests.get("https://the-trivia-api.com/api/questions?limit=5")
        data = response.json()
        preguntas = []
        for q in data:
            pregunta_es = GoogleTranslator(source='auto', target='es').translate(q['question'])
            correcta = GoogleTranslator(source='auto', target='es').translate(q['correctAnswer'])
            incorrectas = [GoogleTranslator(source='auto', target='es').translate(x) for x in q['incorrectAnswers']]
            opciones = incorrectas + [correcta]
            random.shuffle(opciones)
            preguntas.append({"pregunta": pregunta_es, "correcta": correcta, "opciones": opciones})
    st.session_state.preguntas = preguntas
    st.session_state.index = 0
    st.session_state.correctas = 0
    st.session_state.respondido = False
    st.session_state.iniciado = False

# 3) Confirmación de participación
if not st.session_state.iniciado:
    desea = st.radio(
        "¿Quieres hacer un test de cultura general?",
        ["", "Sí", "No"],
        key="desea"
    )
    if desea == "":
        st.write("👉 Por favor selecciona “Sí” o “No” para continuar.")
        st.stop()
    elif desea == "No":
        st.info("Está bien, ¡tal vez otro día! 😄")
        st.stop()
    else:
        st.session_state.iniciado = True

# 4) Lógica del quiz
total = len(st.session_state.preguntas)
idx = st.session_state.index
if idx < total:
    actual = st.session_state.preguntas[idx]
    st.subheader(f"Pregunta {idx+1} de {total}")
    respuesta = st.radio(
        actual["pregunta"],
        actual["opciones"],
        key=f"resp_{idx}"
    )

    # Botón único que cambia de "Responder" a "Siguiente"
    btn = st.empty()
    if not st.session_state.respondido:
        if btn.button("Responder"):
            if respuesta == actual["correcta"]:
                st.success("✅ ¡Correcto!")
                st.session_state.correctas += 1
            else:
                st.error(f"❌ Incorrecto. La respuesta correcta era: {actual['correcta']}")
            st.session_state.respondido = True
    else:
        if btn.button("Siguiente"):
            st.session_state.index += 1
            st.session_state.respondido = False

# 5) Mostrar resultado final
else:
    aciertos = st.session_state.correctas
    st.markdown("## 🎯 Resultado Final")
    if aciertos > total/2:
        st.success(f"🎉 {name}, acertaste {aciertos}/{total}. ¡Buen trabajo!")
    else:
        st.error(f"❌ {name}, solo acertaste {aciertos}/{total}. ¡Sigue practicando!")
    if st.button("Reiniciar Quiz"):
        for key in ["preguntas", "index", "correctas", "respondido", "iniciado", "desea"]:
            st.session_state.pop(key, None)
        st.experimental_rerun()
