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

default_structure_3Bc = {
    "zimni": {
        "Základy STP-III": {
            "Zápočet": {"completed": False, "teacher": ""},
            "Zkouška": {"completed": False, "grade": "", "teacher": ""}
        },
        "Speciální TP-III": {
            "Kurz BZ-III": {"completed": False, "teacher": ""},
            "Kurz PSL-I": {"completed": False, "teacher": ""},
            "Zápočet": {"completed": False, "grade": "", "teacher": ""}
        }
    },
    "letni": {
        "Teorie a didaktika AČR-III": {
            "Zápočet": {"completed": False, "teacher": ""},
            "Zkouška": {"completed": False, "grade": "", "teacher": ""}
        }
    }
}

COHORT = "3. Bc."
DISPLAY_NAME = "Třetí ročník (3. Bc.)"

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
        current_student["subjects"] = deepcopy(default_structure_3Bc)
    else:
        for sem, subs in default_structure_3Bc.items():
            current_student["subjects"].setdefault(sem, {})
            for subj, details in subs.items():
                current_student["subjects"][sem].setdefault(subj, deepcopy(details))

    st.markdown("## Předmětové hodnocení")
    left, right = st.columns(2)

    with left:
        st.subheader("Zimní semestr")
        st.markdown("#### Základy STP-III")
        with st.expander("Detail", expanded=True):
            zim_zap = st.checkbox(
                "Zápočet",
                value=current_student["subjects"]["zimni"]["Základy STP-III"]["Zápočet"]["completed"],
                key="3Bc_STP3_Zap"
            )
            zim_zap_t = st.text_input(
                "Učitel",
                value=current_student["subjects"]["zimni"]["Základy STP-III"]["Zápočet"]["teacher"],
                key="3Bc_STP3_Zap_teacher", max_chars=10
            )
            zim_zk = st.checkbox(
                "Zkouška",
                value=current_student["subjects"]["zimni"]["Základy STP-III"]["Zkouška"]["completed"],
                key="3Bc_STP3_Zk"
            )
            zim_zk_g = st.text_input(
                "Známka",
                value=current_student["subjects"]["zimni"]["Základy STP-III"]["Zkouška"]["grade"],
                key="3Bc_STP3_Zk_grade", max_chars=3
            )
            zim_zk_t = st.text_input(
                "Učitel",
                value=current_student["subjects"]["zimni"]["Základy STP-III"]["Zkouška"]["teacher"],
                key="3Bc_STP3_Zk_teacher", max_chars=10
            )
            current_student["subjects"]["zimni"]["Základy STP-III"]["Zápočet"] = {
                "completed": zim_zap, "teacher": zim_zap_t
            }
            current_student["subjects"]["zimni"]["Základy STP-III"]["Zkouška"] = {
                "completed": zim_zk, "grade": zim_zk_g, "teacher": zim_zk_t
            }
            cond = zim_zap and zim_zk
            st.markdown("Splněno: **" + ("ANO" if cond else "NE") + "**")

        st.markdown("#### Speciální TP-III")
        with st.expander("Detail", expanded=True):
            for subj in ["Kurz BZ-III","Kurz PSL-I","Zápočet"]:
                chk = st.checkbox(
                    subj,
                    value=current_student["subjects"]["zimni"]["Speciální TP-III"][subj]["completed"],
                    key=f"3Bc_SPT3_{subj}"
                )
                teacher = st.text_input(
                    "Učitel",
                    value=current_student["subjects"]["zimni"]["Speciální TP-III"][subj]["teacher"],
                    key=f"3Bc_SPT3_{subj}_teacher", max_chars=10
                )
                current_student["subjects"]["zimni"]["Speciální TP-III"][subj] = {
                    "completed": chk, "teacher": teacher
                }
            cond = all(
                current_student["subjects"]["zimni"]["Speciální TP-III"][s]["completed"]
                for s in ["Kurz BZ-III","Kurz PSL-I","Zápočet"]
            )
            st.markdown("Splněno: **" + ("ANO" if cond else "NE") + "**")

    with right:
        st.subheader("Letní semestr")
        st.markdown("#### Teorie a didaktika AČR-III")
        with st.expander("Detail", expanded=True):
            zap = st.checkbox(
                "Zápočet",
                value=current_student["subjects"]["letni"]["Teorie a didaktika AČR-III"]["Zápočet"]["completed"],
                key="3Bc_TACR3_Zap"
            )
            zap_t = st.text_input(
                "Učitel",
                value=current_student["subjects"]["letni"]["Teorie a didaktika AČR-III"]["Zápočet"]["teacher"],
                key="3Bc_TACR3_Zap_teacher", max_chars=10
            )
            zk = st.checkbox(
                "Zkouška",
                value=current_student["subjects"]["letni"]["Teorie a didaktika AČR-III"]["Zkouška"]["completed"],
                key="3Bc_TACR3_Zk"
            )
            zk_g = st.text_input(
                "Známka",
                value=current_student["subjects"]["letni"]["Teorie a didaktika AČR-III"]["Zkouška"]["grade"],
                key="3Bc_TACR3_Zk_grade", max_chars=3
            )
            zk_t = st.text_input(
                "Učitel",
                value=current_student["subjects"]["letni"]["Teorie a didaktika AČR-III"]["Zkouška"]["teacher"],
                key="3Bc_TACR3_Zk_teacher", max_chars=10
            )
            current_student["subjects"]["letni"]["Teorie a didaktika AČR-III"]["Zápočet"] = {
                "completed": zap, "teacher": zap_t
            }
            current_student["subjects"]["letni"]["Teorie a didaktika AČR-III"]["Zkouška"] = {
                "completed": zk, "grade": zk_g, "teacher": zk_t
            }
            cond = zap and zk
            st.markdown("Splněno: **" + ("ANO" if cond else "NE") + "**")

    if st.button("Uložit hodnocení", key="save_3Bc_" + str(current_student["id_op"])):
        save_student_record(current_student)
        st.success("Hodnocení uloženo!")
