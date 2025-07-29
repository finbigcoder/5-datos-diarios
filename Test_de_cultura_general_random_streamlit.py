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
        response = requests.get(f"https://the-trivia-api.com/api/questions?limit={limit}", timeout=10)
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

# Inicialización del quiz

def init_quiz():
    preguntas = load_and_translate_questions(limit=5)
    if not preguntas:
        st.stop()
    st.session_state.preguntas = preguntas
    st.session_state.idx = 0
    st.session_state.correctas = 0
    st.session_state.respondido = False
    st.session_state.iniciado = False
    st.session_state.feedback = None
    st.session_state.desea = ""

if "preguntas" not in st.session_state:
    init_quiz()

# Pedir nombre\ nname = st.text_input("¿Cuál es tu nombre?", key="name_input")
if not name:
    st.stop()

# Confirmación de participación
if not st.session_state.iniciado:
    st.session_state.desea = st.radio("¿Quieres hacer un test de cultura general?", ["", "Sí", "No"], key="desea")
    if st.session_state.desea == "":
        st.info("👉 Selecciona ‘Sí’ para comenzar o ‘No’ para salir.")
        st.stop()
    if st.session_state.desea == "No":
        st.info("Está bien, ¡tal vez otro día! 😄")
        st.stop()
    st.session_state.iniciado = True

# Callbacks para botones
def submit_answer():
    idx = st.session_state.idx
    actual = st.session_state.preguntas[idx]
    selected = st.session_state.get(f"resp_{idx}")
    if selected == actual["correcta"]:
        st.session_state.correctas += 1
        st.session_state.feedback = (True, "✅ ¡Correcto!")
    else:
        st.session_state.feedback = (False, f"❌ Incorrecto. La respuesta correcta era: {actual['correcta']}")
    st.session_state.respondido = True


def next_question():
    st.session_state.idx += 1
    st.session_state.respondido = False
    st.session_state.feedback = None

# Lógica del quiz
total = len(st.session_state.preguntas)
idx = st.session_state.idx
if idx < total:
    actual = st.session_state.preguntas[idx]
    st.subheader(f"Pregunta {idx+1} de {total}")
    st.radio(actual["pregunta"], actual["opciones"], key=f"resp_{idx}")

    if not st.session_state.respondido:
        st.button("Responder", on_click=submit_answer, key=f"btn_resp_{idx}")
    else:
        ok, msg = st.session_state.feedback
        st.success(msg) if ok else st.error(msg)
        st.button("Siguiente", on_click=next_question, key=f"btn_sig_{idx}")
# Resultado final
else:
    aciertos = st.session_state.correctas
    st.markdown("## 🎯 Resultado Final")
    if aciertos > total/2:
        st.success(f"🎉 {name}, acertaste {aciertos}/{total}. ¡Buen trabajo!")
    else:
        st.error(f"❌ {name}, solo acertaste {aciertos}/{total}. ¡Sigue practicando!")
    st.button("Reiniciar Quiz", on_click=init_quiz)
