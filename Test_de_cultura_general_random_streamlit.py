import requests
from deep_translator import GoogleTranslator
import random
import streamlit as st
import time
from datetime import datetime, timezone
import pandas as pd
from typing import Optional

# Optional Supabase backend (if secrets provided)
_SUPABASE_OK = False
try:
    from supabase import create_client, Client  # pip install supabase
    _SUPABASE_OK = True
except Exception:
    _SUPABASE_OK = False

# ------------------------------
# Page config
# ------------------------------
st.set_page_config(page_title="Test de Cultura General", page_icon="🎓", layout="centered")
st.title("🎓 Test de Cultura General")

TOP_N = 25            # leaderboard length
USE_DURATION_TIE = True  # rank by score desc, then time asc

# ------------------------------
# Backend selection
# ------------------------------
def _has_supabase_secrets() -> bool:
    try:
        _ = st.secrets["supabase"]["url"]
        _ = st.secrets["supabase"]["key"]
        return True
    except Exception:
        return False

@st.cache_resource
def get_supabase() -> Optional["Client"]:
    if not (_SUPABASE_OK and _has_supabase_secrets()):
        return None
    return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

SB = get_supabase()

# Local CSV fallback (ephemeral in many hosts)
@st.cache_resource
def get_local_path() -> str:
    return "quiz_scores_local.csv"

def local_read_df() -> pd.DataFrame:
    path = get_local_path()
    try:
        df = pd.read_csv(path)
        # ensure dtypes exist
        if "submitted_at" in df.columns:
            df["submitted_at"] = pd.to_datetime(df["submitted_at"], utc=True, errors="coerce")
        return df
    except Exception:
        return pd.DataFrame(columns=["player_name","score","duration_seconds","submitted_at"])

def local_append_row(row: dict):
    path = get_local_path()
    df = local_read_df()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(path, index=False)

# ------------------------------
# Data/translation
# ------------------------------
def load_and_translate_questions(limit=5):
    """
    Descarga preguntas y las traduce al español.
    Retorna lista[dict]: {pregunta, correcta, opciones}
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
            pregunta_es = GoogleTranslator(source="auto", target="es").translate(q["question"])
            correcta_es = GoogleTranslator(source="auto", target="es").translate(q["correctAnswer"])
            incorrectas_es = [
                GoogleTranslator(source="auto", target="es").translate(opt)
                for opt in q["incorrectAnswers"]
            ]
        except Exception as e:
            st.error(f"Error traduciendo preguntas: {e}")
            return []

        opciones = incorrectas_es + [correcta_es]
        random.shuffle(opciones)
        preguntas.append({"pregunta": pregunta_es, "correcta": correcta_es, "opciones": opciones})
    return preguntas

# ------------------------------
# Leaderboard helpers
# ------------------------------
def save_score(player_name: str, score: int, duration_seconds: Optional[float]):
    now_iso = datetime.now(timezone.utc).isoformat()
    payload = {
        "player_name": player_name.strip(),
        "score": int(score),
        "duration_seconds": float(duration_seconds) if duration_seconds is not None else None,
        "submitted_at": now_iso,
    }

    if SB is not None:
        # Supabase insert
        res = SB.table("quiz_scores").insert(payload).execute()
        if getattr(res, "error", None):
            st.warning("No se pudo guardar en Supabase. Usando almacenamiento local.")
            local_append_row(payload)
    else:
        # Local CSV fallback
        local_append_row(payload)

def fetch_top_scores(limit=TOP_N) -> pd.DataFrame:
    if SB is not None:
        # Order: score desc, duration asc (nulls last), submitted_at asc
        order = ["score.desc"]
        if USE_DURATION_TIE:
            order.append("duration_seconds.asc.nullslast")
        order.append("submitted_at.asc")
        res = SB.table("quiz_scores").select("*").order(*order).limit(limit).execute()
        rows = res.data or []
        df = pd.DataFrame(rows)
        if not df.empty and "submitted_at" in df.columns:
            df["submitted_at"] = pd.to_datetime(df["submitted_at"], utc=True, errors="coerce")
        return df
    else:
        df = local_read_df()
        if df.empty:
            return df
        # same sort locally
        sort_cols = ["score"]
        ascending = [False]
        if USE_DURATION_TIE:
            sort_cols.append("duration_seconds")
            ascending.append(True)
        sort_cols.append("submitted_at"); ascending.append(True)
        df = df.sort_values(sort_cols, ascending=ascending)
        return df.head(limit)

def dense_rank(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    sort_cols = ["score"]; ascending = [False]
    if USE_DURATION_TIE:
        sort_cols.append("duration_seconds"); ascending.append(True)
    sort_cols.append("submitted_at"); ascending.append(True)
    df = df.sort_values(sort_cols, ascending=ascending).reset_index(drop=True)
    ranks = []
    last_key = None
    r = 0
    for _, row in df.iterrows():
        key = (row["score"], row.get("duration_seconds", None))
        if key != last_key:
            r += 1
            last_key = key
        ranks.append(r)
    df["rank"] = ranks
    return df

def fetch_player_best(player_name: str) -> Optional[pd.Series]:
    name = player_name.strip()
    if not name:
        return None
    if SB is not None:
        res = SB.table("quiz_scores").select("*").eq("player_name", name).execute()
        mine = pd.DataFrame(res.data or [])
    else:
        df = local_read_df()
        mine = df[df["player_name"].astype(str).str.strip() == name]

    if mine.empty:
        return None
    ranked = dense_rank(mine)
    best = ranked.sort_values(["rank","score","duration_seconds"], ascending=[True,False,True]).iloc[0]
    return best

# ------------------------------
# Quiz state
# ------------------------------
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
    st.session_state.quiz_started_at = None
    st.session_state.just_finished = False

if "preguntas" not in st.session_state:
    init_quiz()

# ------------------------------
# UI – Player name & consent
# ------------------------------
declare_name = st.text_input("¿Cuál es tu nombre para el leaderboard?", key="name_input", max_chars=24)
if not declare_name:
    st.stop()

if not st.session_state.iniciado:
    desea = st.radio("¿Quieres hacer un test de cultura general?", ["", "Sí", "No"], key="desea")
    if desea == "":
        st.info("👉 Selecciona ‘Sí’ para comenzar o ‘No’ para salir.")
        st.stop()
    if desea == "No":
        st.info("Está bien, ¡tal vez otro día! 😄")
        st.stop()
    # Marcar inicio y tiempo de inicio
    st.session_state.iniciado = True
    st.session_state.quiz_started_at = time.monotonic()
    st.success("¡Comencemos!")

# ------------------------------
# Callbacks
# ------------------------------
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

def restart_quiz():
    init_quiz()

# ------------------------------
# Quiz flow
# ------------------------------
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
        (st.success if ok else st.error)(msg)
        st.button("Siguiente", on_click=next_question, key=f"btn_sig_{idx}")

else:
    # Resultado final
    aciertos = st.session_state.correctas
    duration_seconds = None
    if st.session_state.quiz_started_at is not None:
        duration_seconds = max(0.0, time.monotonic() - st.session_state.quiz_started_at)

    st.markdown("## 🎯 Resultado Final")
    if aciertos > total / 2:
        st.success(f"🎉 {declare_name}, acertaste {aciertos}/{total}. ¡Buen trabajo!")
    else:
        st.error(f"❌ {declare_name}, solo acertaste {aciertos}/{total}. ¡Sigue practicando!")

    # Guardar puntaje
    with st.form("save_score_form", clear_on_submit=False):
        agree = st.checkbox("Acepto que mi nombre aparezca en el leaderboard público.")
        submitted = st.form_submit_button("Guardar mi puntaje")
        if submitted:
            if not agree:
                st.warning("Debes aceptar para guardar tu puntaje.")
            else:
                save_score(declare_name, aciertos, duration_seconds)
                st.session_state.just_finished = True
                st.success("✅ Puntaje guardado. Desliza abajo para ver el podio y el leaderboard.")

    st.button("Reiniciar Quiz", on_click=restart_quiz, key="btn_restart")

# ------------------------------
# Leaderboard & Podium section
# ------------------------------
st.divider()
st.subheader("🏆 Podio & Leaderboard")

# Info sobre backend usado
if SB is None:
    st.caption("💾 Modo local (CSV, no persistente en reinicios). Configura Supabase en secrets para persistir.")

df = fetch_top_scores(limit=TOP_N)
if df.empty:
    st.info("Aún no hay puntajes guardados. ¡Sé el primero!")
else:
    # Rank dense
    df_ranked = dense_rank(df)

    # Podio (Top 3)
    top3 = df_ranked[df_ranked["rank"] <= 3].copy()
    cols = st.columns(3, gap="large")
    podium_emojis = {1: "🥇", 2: "🥈", 3: "🥉"}

    # Visualmente: #2, #1, #3 para centrar al ganador
    for i, place in enumerate([2, 1, 3]):
        slot = cols[i]
        row = top3[top3["rank"] == place]
        if not row.empty:
            r = row.iloc[0]
            slot.markdown(f"### {podium_emojis[place]} #{place}")
            slot.markdown(f"**{r['player_name']}**")
            slot.markdown(f"Puntaje: **{int(r['score'])}**")
            if USE_DURATION_TIE and pd.notna(r.get("duration_seconds")):
                slot.caption(f"{float(r['duration_seconds']):.1f} s")

    st.divider()

    # Tabla leaderboard
    show_df = df_ranked[["rank", "player_name", "score", "duration_seconds", "submitted_at"]].copy()
    show_df.rename(
        columns={
            "rank": "Pos",
            "player_name": "Nombre",
            "score": "Puntaje",
            "duration_seconds": "Tiempo (s)",
            "submitted_at": "Fecha (UTC)",
        },
        inplace=True,
    )
    st.dataframe(show_df, use_container_width=True, hide_index=True)

    # Mostrar mejor posición del jugador actual
    if declare_name:
        my_best = fetch_player_best(declare_name)
        if my_best is not None:
            extra = ""
            if USE_DURATION_TIE and pd.notna(my_best.get("duration_seconds")):
                extra = f" en {float(my_best['duration_seconds']):.1f}s"
            st.info(f"**{declare_name}**, tu mejor posición es **#{int(my_best['rank'])}** con **{int(my_best['score'])}**{extra}.")

# ------------------------------
# Footer
# ------------------------------
st.caption("Tip: el ranking ordena por puntaje (mayor mejor), luego por tiempo (menor mejor).")
