import requests
from deep_translator import GoogleTranslator
import random
import streamlit as st

# Configuración de la página\ nst.set_page_config(page_title="Test de Cultura General", page_icon="🎓")
st.title("🎓 Test de Cultura General")

@st.cache_data(show_spinner=False)
def load_and_translate_questions(limit=5):
    """
    Descarga preguntas de trivia y las traduce al español. Retorna lista de dicts.
    """
    try:
        response = requests.get(
            f"https://the-trivia-api.com/api/questions?limit={limit}", timeout=10
        )
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        st.error(f"Error cargando preguntas: {e}")
        return []

    preguntas = []
    for q in data:
        try:
            pregunta_es = GoogleTranslator(source='auto', target='es').translate(q['question'])
            correcta_es = GoogleTranslator(source='auto', target='es').translate(q['correctAnswer'])
            incorrectas_es = [GoogleTranslator(source='auto', target='es').translate(x)
                               for x in q['incorrectAnswers']]
        except Exception as e:
            st.error(f"Error traduciendo preguntas: {e}")
            return []
        opciones = incorrectas_es + [correcta_es]
        random.shuffle(opciones)
        preguntas.append({"pregunta": pregunta_es, "correcta": correcta_es, "opciones": opciones})
    return preguntas

# 1) Precarga de preguntas
if "preguntas" not in st.session_state:
    with st.spinner("Cargando y traduciendo preguntas..."):
        preguntas = load_and_translate_questions(limit=5)
    if not preguntas:
        st.stop()
    st.session_state.preguntas = preguntas
    st.session_state.idx = 0
    st.session_state.correctas = 0
    st.session_state.respondido = False
    st.session_state.iniciado = False

# 2) Pedir nombre
name = st.text_input("¿Cuál es tu nombre?", key="name_input")
if not name:
    st.stop()

# 3) Confirmación de participación
if not st.session_state.iniciado:
    desea = st.radio(
        "¿Quieres hacer un test de cultura general?",
        ["", "Sí", "No"],
        key="desea"
    )
    if desea == "":
        st.info("👉 Selecciona ‘Sí’ para comenzar o ‘No’ para salir.")
        st.stop()
    if desea == "No":
        st.info("Está bien, ¡tal vez otro día! 😄")
        st.stop()
    st.session_state.iniciado = True

# 4) Lógica del quiz
total = len(st.session_state.preguntas)
idx = st.session_state.idx
if idx < total:
    actual = st.session_state.preguntas[idx]
    st.subheader(f"Pregunta {idx+1} de {total}")
    respuesta = st.radio(actual["pregunta"], actual["opciones"], key=f"resp_{idx}")

    if not st.session_state.respondido:
        if st.button("Responder", key=f"btn_resp_{idx}"):
            if respuesta == actual["correcta"]:
                st.success("✅ ¡Correcto!")
                st.session_state.correctas += 1
            else:
                st.error(f"❌ Incorrecto. La respuesta correcta era: {actual['correcta']}")
            st.session_state.respondido = True
    else:
        if st.button("Siguiente", key=f"btn_sig_{idx}"):
            st.session_state.idx += 1
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
        for var in ["preguntas", "idx", "correctas", "respondido", "iniciado", "desea"]:
            st.session_state.pop(var, None)
        # Se recarga automáticamente tras interacción

