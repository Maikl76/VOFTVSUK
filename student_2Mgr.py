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
        # Uložíme pouze sloupec 'subjects', bez debug výpisů
        response = (
            supabase
            .table("students")
            .update({"subjects": student["subjects"]})
            .eq("id_op", student["id_op"])
            .execute()
        )
        return response.data
    except Exception as e:
        st.error("Chyba při ukládání: " + str(e))
        return None

default_structure_2Mgr = {
    "zimni": {
        "Speciální TP-2": {
            "Kurz BZ-IV": {"completed": False, "teacher": "", "instruktor": False},
            "Kurz VL-IV": {"completed": False, "teacher": "", "instruktor": False},
            "Kurz PSL-II": {"completed": False, "teacher": "", "instruktor": False},
            "Klasifikovaný zápočet": {"completed": False, "grade": "", "teacher": ""},
            "Splněno": {"value": "NE"}
        }
    },
    "letni": {
        "Teorie a didaktika AČR-3": {
            "Zápočet 1": {"completed": False, "teacher": ""},
            "Zkouška": {"completed": False, "grade": "", "teacher": ""},
            "Splněno": {"value": "NE"}
        }
    }
}

COHORT = "2. Mgr."
DISPLAY_NAME = "Pátý ročník (2. Mgr.)"

def run_student():
    st.title("Studenti - " + DISPLAY_NAME)
    students = load_students()
    cohort_students = [s for s in students if s.get("cohort") == COHORT]
    if not cohort_students:
        st.info("Žádní studenti nejsou zaregistrováni.")
        return

    df = pd.DataFrame(cohort_students)
    st.dataframe(df, use_container_width=True)

    idx = st.selectbox(
        "Vyberte studenta",
        options=df.index,
        format_func=lambda i: f"{df.loc[i,'hodnost']} {df.loc[i,'first_name']} {df.loc[i,'last_name']}"
    )
    current_student = deepcopy(cohort_students[idx])

    # inicializace subjects
    if "subjects" not in current_student:
        current_student["subjects"] = deepcopy(default_structure_2Mgr)
    else:
        for sem, subs in default_structure_2Mgr.items():
            current_student["subjects"].setdefault(sem, {})
            for subj, details in subs.items():
                current_student["subjects"][sem].setdefault(subj, deepcopy(details))

    st.markdown("## Předmětové hodnocení")
    left, right = st.columns(2)

    with left:
        st.subheader("Zimní semestr")
        st.markdown("#### Speciální TP-2")
        with st.expander("Detail", expanded=True):
            # Kurz BZ-IV
            bziv_chk = st.checkbox(
                "Kurz BZ-IV",
                value=current_student["subjects"]["zimni"]["Speciální TP-2"]["Kurz BZ-IV"]["completed"],
                key="2Mgr_SPT2_BZIV"
            )
            bziv_instr = st.checkbox(
                "Instruktor",
                value=current_student["subjects"]["zimni"]["Speciální TP-2"]["Kurz BZ-IV"].get("instruktor", False),
                key="2Mgr_SPT2_BZIV_instr"
            )
            bziv_teacher = st.text_input(
                "Učitel",
                value=current_student["subjects"]["zimni"]["Speciální TP-2"]["Kurz BZ-IV"]["teacher"],
                key="2Mgr_SPT2_BZIV_teacher", max_chars=10
            )
            current_student["subjects"]["zimni"]["Speciální TP-2"]["Kurz BZ-IV"] = {
                "completed": bziv_chk, "instruktor": bziv_instr, "teacher": bziv_teacher
            }

            # ostatní položky obdobně...
            # (zachovejte původní logiku pro Kurz VL-IV, PSL-II, Klasifikovaný zápočet)

    if st.button("Uložit hodnocení", key="save_2Mgr_" + str(current_student["id_op"])):
        save_student_record(current_student)
        st.success("Hodnocení uloženo!")
