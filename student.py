import streamlit as st
import pandas as pd
import datetime
from copy import deepcopy
from supabase import create_client, Client

st.markdown("""
<style>
.stTextInput>div>div>input {
    max-width: 150px;
}
</style>
""", unsafe_allow_html=True)

# ===== KONFIGURACE SUPABASE =====
SUPABASE_URL = st.secrets["supabase"]["supabase_url"]
SUPABASE_KEY = st.secrets["supabase"]["supabase_key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# =================================

def load_students():
    try:
        resp = supabase.table("students").select("*").execute()
        return resp.data or []
    except Exception as e:
        st.error("Chyba při načítání studentů: " + str(e))
        return []

def save_student_record(student):
    try:
        resp = (
            supabase
            .table("students")
            .update({"subjects": student["subjects"]})
            .eq("id_op", student["id_op"])
            .execute()
        )
        return resp.data
    except Exception as e:
        st.error("Chyba při ukládání: " + str(e))
        return None

default_structure_1Bc = {
    "zimni": {
        "Teorie a didaktika AČR-I": {"completed": False, "teacher": ""}
    },
    "letni": {
        "Základy STP-I": {
            "Vojenské lezení": {"completed": False, "teacher": ""},
            "Boj zblízka": {"completed": False, "teacher": ""},
            "Teoretický test": {"completed": False, "teacher": ""},
            "Zápočet": {"completed": False, "teacher": ""}
        },
        "Speciální TP-I": {
            "Kurz BZ-I": {"completed": False, "teacher": ""},
            "Kurz VL-I": {"completed": False, "teacher": ""},
            "Kurz PSL": {"completed": False, "teacher": ""},
            "STP-I": {"completed": False, "teacher": ""},
            "Zápočet": {"completed": False, "teacher": ""}
        }
    }
}

COHORT = "1. Bc."
DISPLAY_NAME = "První ročník (1. Bc.)"

def run_student():
    st.title("Studenti - " + DISPLAY_NAME)
    students = load_students()
    cohort_students = [s for s in students if s.get("cohort") == COHORT]
    if not cohort_students:
        st.info("Žádní studenti nejsou zaregistrováni.")
        return

    # schováme id, subjects a is_graduated
    df = pd.DataFrame(cohort_students)
    df = df.drop(columns=["id", "subjects", "is_graduated"], errors="ignore")
    st.dataframe(df, use_container_width=True)

    idx = st.selectbox(
        "Vyberte studenta",
        options=df.index,
        format_func=lambda i: f"{cohort_students[i]['hodnost']} {cohort_students[i]['first_name']} {cohort_students[i]['last_name']}"
    )
    current_student = deepcopy(cohort_students[idx])

    # inicializace subjects
    if "subjects" not in current_student:
        current_student["subjects"] = deepcopy(default_structure_1Bc)
    else:
        for sem, subs in default_structure_1Bc.items():
            current_student["subjects"].setdefault(sem, {})
            for subj, details in subs.items():
                current_student["subjects"][sem].setdefault(subj, deepcopy(details))

    st.markdown("## Předmětové hodnocení")
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Zimní semestr")
        st.markdown("#### Teorie a didaktika AČR-I")
        with st.expander("Detail hodnocení", expanded=True):
            chk = st.checkbox(
                "Zápočet",
                value=current_student["subjects"]["zimni"]["Teorie a didaktika AČR-I"]["completed"],
                key="1Bc_zim_TACRI"
            )
            teacher = st.text_input(
                "Učitel",
                value=current_student["subjects"]["zimni"]["Teorie a didaktika AČR-I"]["teacher"],
                key="1Bc_zim_TACRI_teacher", max_chars=10
            )
            current_student["subjects"]["zimni"]["Teorie a didaktika AČR-I"] = {
                "completed": chk, "teacher": teacher
            }
            st.markdown("Splněno: **" + ("ANO" if chk else "NE") + "**")

    with c2:
        st.subheader("Letní semestr")
        st.markdown("### Základy STP-I")
        with st.expander("Detail hodnocení", expanded=True):
            for subj in ["Vojenské lezení", "Boj zblízka", "Teoretický test", "Zápočet"]:
                chk = st.checkbox(
                    subj,
                    value=current_student["subjects"]["letni"]["Základy STP-I"][subj]["completed"],
                    key=f"1Bc_let_STP1_{subj}"
                )
                teacher = st.text_input(
                    "Učitel",
                    value=current_student["subjects"]["letni"]["Základy STP-I"][subj]["teacher"],
                    key=f"1Bc_let_STP1_{subj}_teacher", max_chars=10
                )
                current_student["subjects"]["letni"]["Základy STP-I"][subj] = {
                    "completed": chk, "teacher": teacher
                }
            cond = all(
                current_student["subjects"]["letni"]["Základy STP-I"][s]["completed"]
                for s in ["Vojenské lezení", "Boj zblízka", "Teoretický test", "Zápočet"]
            )
            st.markdown("Splněno: **" + ("ANO" if cond else "NE") + "**")

        st.markdown("### Speciální TP-I")
        with st.expander("Detail hodnocení", expanded=True):
            for subj in ["Kurz BZ-I", "Kurz VL-I", "Kurz PSL", "STP-I", "Zápočet"]:
                chk = st.checkbox(
                    subj,
                    value=current_student["subjects"]["letni"]["Speciální TP-I"][subj]["completed"],
                    key=f"1Bc_let_SPT1_{subj}"
                )
                teacher = st.text_input(
                    "Učitel",
                    value=current_student["subjects"]["letni"]["Speciální TP-I"][subj]["teacher"],
                    key=f"1Bc_let_SPT1_{subj}_teacher", max_chars=10
                )
                current_student["subjects"]["letni"]["Speciální TP-I"][subj] = {
                    "completed": chk, "teacher": teacher
                }
            cond = all(
                current_student["subjects"]["letni"]["Speciální TP-I"][s]["completed"]
                for s in ["Kurz BZ-I", "Kurz VL-I", "Kurz PSL", "STP-I", "Zápočet"]
            )
            st.markdown("Splněno: **" + ("ANO" if cond else "NE") + "**")

    if st.button("Uložit hodnocení", key="save_1Bc_" + str(current_student["id_op"])):
        save_student_record(current_student)
        st.success("Hodnocení uloženo!")
