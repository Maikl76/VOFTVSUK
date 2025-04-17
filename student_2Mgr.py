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
    st.title("Systém studentů - " + DISPLAY_NAME)
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
        with st.expander("Detail hodnocení", expanded=True):
            bziv_chk = st.checkbox(
                "Kurz BZ-IV",
                value=current_student["subjects"]["zimni"]["Speciální TP-2"]["Kurz BZ-IV"]["completed"],
                key="2Mgr_SPT2_BZIV"
            )
            bziv_instr = st.checkbox(
                "Instruktor",
                value=current_student["subjects"]["zimni"]["Speciální TP-2"]["Kurz BZ-IV"]["instruktor"],
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

            vliv_chk = st.checkbox(
                "Kurz VL-IV",
                value=current_student["subjects"]["zimni"]["Speciální TP-2"]["Kurz VL-IV"]["completed"],
                key="2Mgr_SPT2_VLIV"
            )
            vliv_instr = st.checkbox(
                "Instruktor",
                value=current_student["subjects"]["zimni"]["Speciální TP-2"]["Kurz VL-IV"]["instruktor"],
                key="2Mgr_SPT2_VLIV_instr"
            )
            vliv_teacher = st.text_input(
                "Učitel",
                value=current_student["subjects"]["zimni"]["Speciální TP-2"]["Kurz VL-IV"]["teacher"],
                key="2Mgr_SPT2_VLIV_teacher", max_chars=10
            )
            current_student["subjects"]["zimni"]["Speciální TP-2"]["Kurz VL-IV"] = {
                "completed": vliv_chk, "instruktor": vliv_instr, "teacher": vliv_teacher
            }

            psl_chk = st.checkbox(
                "Kurz PSL-II",
                value=current_student["subjects"]["zimni"]["Speciální TP-2"]["Kurz PSL-II"]["completed"],
                key="2Mgr_SPT2_PSL"
            )
            psl_instr = st.checkbox(
                "Instruktor",
                value=current_student["subjects"]["zimni"]["Speciální TP-2"]["Kurz PSL-II"]["instruktor"],
                key="2Mgr_SPT2_PSL_instr"
            )
            psl_teacher = st.text_input(
                "Učitel",
                value=current_student["subjects"]["zimni"]["Speciální TP-2"]["Kurz PSL-II"]["teacher"],
                key="2Mgr_SPT2_PSL_teacher", max_chars=10
            )
            current_student["subjects"]["zimni"]["Speciální TP-2"]["Kurz PSL-II"] = {
                "completed": psl_chk, "instruktor": psl_instr, "teacher": psl_teacher
            }

            klas_chk = st.checkbox(
                "Klasifikovaný zápočet",
                value=current_student["subjects"]["zimni"]["Speciální TP-2"]["Klasifikovaný zápočet"]["completed"],
                key="2Mgr_SPT2_KLAS"
            )
            klas_grade = st.text_input(
                "Známka",
                value=current_student["subjects"]["zimni"]["Speciální TP-2"]["Klasifikovaný zápočet"]["grade"],
                key="2Mgr_SPT2_KLAS_grade", max_chars=3
            )
            klas_teacher = st.text_input(
                "Učitel",
                value=current_student["subjects"]["zimni"]["Speciální TP-2"]["Klasifikovaný zápočet"]["teacher"],
                key="2Mgr_SPT2_KLAS_teacher", max_chars=10
            )
            current_student["subjects"]["zimni"]["Speciální TP-2"]["Klasifikovaný zápočet"] = {
                "completed": klas_chk, "grade": klas_grade, "teacher": klas_teacher
            }

            cond = (
                bziv_chk and vliv_chk and psl_chk and klas_chk
            )
            current_student["subjects"]["zimni"]["Speciální TP-2"]["Splněno"] = {"value": "ANO" if cond else "NE"}
            st.markdown("Splněno: **" + ("ANO" if cond else "NE") + "**")

    with right:
        st.subheader("Letní semestr")
        st.markdown("#### Teorie a didaktika AČR-3")
        with st.expander("Detail hodnocení", expanded=True):
            zap1_chk = st.checkbox(
                "Zápočet 1",
                value=current_student["subjects"]["letni"]["Teorie a didaktika AČR-3"]["Zápočet 1"]["completed"],
                key="2Mgr_TACR3_ZAP1"
            )
            zap1_teacher = st.text_input(
                "Učitel",
                value=current_student["subjects"]["letni"]["Teorie a didaktika AČR-3"]["Zápočet 1"]["teacher"],
                key="2Mgr_TACR3_ZAP1_teacher", max_chars=10
            )
            zk_chk = st.checkbox(
                "Zkouška",
                value=current_student["subjects"]["letni"]["Teorie a didaktika AČR-3"]["Zkouška"]["completed"],
                key="2Mgr_TACR3_ZK"
            )
            zk_grade = st.text_input(
                "Známka",
                value=current_student["subjects"]["letni"]["Teorie a didaktika AČR-3"]["Zkouška"]["grade"],
                key="2Mgr_TACR3_ZK_grade", max_chars=3
            )
            zk_teacher = st.text_input(
                "Učitel",
                value=current_student["subjects"]["letni"]["Teorie a didaktika AČR-3"]["Zkouška"]["teacher"],
                key="2Mgr_TACR3_ZK_teacher", max_chars=10
            )
            current_student["subjects"]["letni"]["Teorie a didaktika AČR-3"]["Zápočet 1"] = {
                "completed": zap1_chk, "teacher": zap1_teacher
            }
            current_student["subjects"]["letni"]["Teorie a didaktika AČR-3"]["Zkouška"] = {
                "completed": zk_chk, "grade": zk_grade, "teacher": zk_teacher
            }
            cond = zap1_chk and zk_chk
            current_student["subjects"]["letni"]["Teorie a didaktika AČR-3"]["Splněno"] = {"value": "ANO" if cond else "NE"}
            st.markdown("Splněno: **" + ("ANO" if cond else "NE") + "**")

    if st.button("Uložit hodnocení", key="save_2Mgr_" + str(current_student["id_op"])):
        save_student_record(current_student)
        st.success("Hodnocení uloženo!")
