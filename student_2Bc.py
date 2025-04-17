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

default_structure_2Bc = {
    "zimni": {
        "Základy STP-II": {
            "Vojenské lezení": {"completed": False, "teacher": ""},
            "Boj zblízka":    {"completed": False, "teacher": ""},
            "Teoretický test":{"completed": False, "teacher": ""},
            "Zápočet":        {"completed": False, "teacher": ""}
        }
    },
    "letni": {
        "Teorie a didaktika AČR-II": {"completed": False, "teacher": ""},
        "Speciální TP-II": {
            "Kurz BZ-II": {"completed": False, "teacher": ""},
            "Kurz VL-II": {"completed": False, "teacher": ""},
            "Kurz VPL-I": {"completed": False, "teacher": ""},
            "Kurz ZP-I":  {"completed": False, "teacher": ""},
            "Zápočet":    {"completed": False, "teacher": ""}
        }
    }
}

COHORT = "2. Bc."
DISPLAY_NAME = "Druhý ročník (2. Bc.)"

def run_student():
    st.title("Systém studentů - " + DISPLAY_NAME)
    students = load_students()
    cohort_students = [s for s in students if s.get("cohort") == COHORT]
    if not cohort_students:
        st.info("Žádní studenti z tohoto ročníku nejsou zaregistrováni.")
        return

    df = pd.DataFrame(cohort_students)
    st.dataframe(df, use_container_width=True)

    idx = st.selectbox(
        "Vyberte studenta",
        options=df.index,
        format_func=lambda i: f"{df.loc[i,'hodnost']} {df.loc[i,'first_name']} {df.loc[i,'last_name']}"
    )
    current_student = deepcopy(cohort_students[idx])

    # inicializace nebo doplnění subjects
    if "subjects" not in current_student:
        current_student["subjects"] = deepcopy(default_structure_2Bc)
    else:
        for sem, subs in default_structure_2Bc.items():
            current_student["subjects"].setdefault(sem, {})
            for subj, details in subs.items():
                current_student["subjects"][sem].setdefault(subj, deepcopy(details))

    st.markdown("## Předmětové hodnocení")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Zimní semestr")
        st.markdown("#### Základy STP-II")
        with st.expander("Detail hodnocení", expanded=True):
            for subj in ["Vojenské lezení","Boj zblízka","Teoretický test","Zápočet"]:
                chk = st.checkbox(
                    subj,
                    value=current_student["subjects"]["zimni"]["Základy STP-II"][subj]["completed"],
                    key=f"2Bc_zim_STP2_{subj}"
                )
                teacher = st.text_input(
                    "Učitel, který zapsal",
                    value=current_student["subjects"]["zimni"]["Základy STP-II"][subj]["teacher"],
                    key=f"2Bc_zim_STP2_{subj}_teacher",
                    max_chars=10
                )
                current_student["subjects"]["zimni"]["Základy STP-II"][subj] = {
                    "completed": chk, "teacher": teacher
                }
            cond = all(
                current_student["subjects"]["zimni"]["Základy STP-II"][s]["completed"]
                for s in ["Vojenské lezení","Boj zblízka","Teoretický test","Zápočet"]
            )
            st.markdown("Splněno: **" + ("ANO" if cond else "NE") + "**")

    with col2:
        st.subheader("Letní semestr")
        st.markdown("### Teorie a didaktika AČR-II")
        with st.expander("Detail hodnocení", expanded=True):
            chk = st.checkbox(
                "Zápočet",
                value=current_student["subjects"]["letni"].get("Teorie a didaktika AČR-II", {}).get("completed", False),
                key="2Bc_let_TACR2_Zapo"
            )
            teacher = st.text_input(
                "Učitel, který zapsal",
                value=current_student["subjects"]["letni"].get("Teorie a didaktika AČR-II", {}).get("teacher", ""),
                key="2Bc_let_TACR2_Zapo_teacher",
                max_chars=10
            )
            current_student["subjects"]["letni"]["Teorie a didaktika AČR-II"] = {
                "completed": chk, "teacher": teacher
            }
            st.markdown("Splněno: **" + ("ANO" if chk else "NE") + "**")

        st.markdown("### Speciální TP-II")
        with st.expander("Detail hodnocení", expanded=True):
            for subj in ["Kurz BZ-II","Kurz VL-II","Kurz VPL-I","Kurz ZP-I","Zápočet"]:
                chk = st.checkbox(
                    subj,
                    value=current_student["subjects"]["letni"]["Speciální TP-II"][subj]["completed"],
                    key=f"2Bc_let_SPT2_{subj}"
                )
                teacher = st.text_input(
                    "Učitel, který zapsal",
                    value=current_student["subjects"]["letni"]["Speciální TP-II"][subj]["teacher"],
                    key=f"2Bc_let_SPT2_{subj}_teacher",
                    max_chars=10
                )
                current_student["subjects"]["letni"]["Speciální TP-II"][subj] = {
                    "completed": chk, "teacher": teacher
                }
            cond = all(
                current_student["subjects"]["letni"]["Speciální TP-II"][s]["completed"]
                for s in ["Kurz BZ-II","Kurz VL-II","Kurz VPL-I","Kurz ZP-I","Zápočet"]
            )
            st.markdown("Splněno: **" + ("ANO" if cond else "NE") + "**")

    if st.button("Uložit hodnocení", key="save_2Bc_" + str(current_student["id_op"])):
        save_student_record(current_student)
        st.success("Hodnocení uloženo!")
