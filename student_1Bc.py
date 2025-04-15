import streamlit as st
import pandas as pd
import json, os, datetime
from copy import deepcopy

# CSS pro omezení šířky vstupních polí
st.markdown("""
<style>
.stTextInput>div>div>input {
    max-width: 150px;
}
</style>
""", unsafe_allow_html=True)

DATA_FILE = "students.json"

def load_students():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return []

def save_students(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

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
    st.title("Systém studentů - " + DISPLAY_NAME)
    students = load_students()
    cohort_students = [s for s in students if s.get("cohort") == COHORT]
    if not cohort_students:
        st.info("Žádní studenti z tohoto ročníku nejsou zaregistrováni.")
        return

    df = pd.DataFrame(cohort_students)
    st.dataframe(df, use_container_width=True)
    
    selected_idx = st.selectbox("Vyberte studenta", options=df.index,
                                format_func=lambda i: f"{df.loc[i, 'hodnost']} {df.loc[i, 'first_name']} {df.loc[i, 'last_name']}")
    current_student = deepcopy(cohort_students[selected_idx])
    if "subjects" not in current_student:
        current_student["subjects"] = deepcopy(default_structure_1Bc)
    else:
        for sem in default_structure_1Bc:
            current_student["subjects"].setdefault(sem, {})
            for subj, details in default_structure_1Bc[sem].items():
                current_student["subjects"][sem].setdefault(subj, deepcopy(details))
    
    st.markdown("## Předmětové hodnocení")

    # Rozložení do dvou sloupců – levý: Zimní semestr, pravý: Letní semestr
    col_left, col_right = st.columns(2)

    ## Levý sloupec – Zimní semestr
    with col_left:
        st.subheader("Zimní semestr")
        st.markdown("#### Teorie a didaktika AČR-I")
        with st.expander("Detail hodnocení", expanded=True):
            col1, col2 = st.columns([0.3, 0.3])
            with col1:
                # Přidán text "Zápočet" jako popisek checkboxu
                zim_chk = st.checkbox("Zápočet", value=current_student["subjects"]["zimni"]["Teorie a didaktika AČR-I"].get("completed", False), key="1Bc_zim_TACRI")
            with col2:
                zim_teacher = st.text_input("Učitel, který zapsal", 
                                             value=current_student["subjects"]["zimni"]["Teorie a didaktika AČR-I"].get("teacher", ""),
                                             key="1Bc_zim_TACRI_teacher", max_chars=10)
            current_student["subjects"]["zimni"]["Teorie a didaktika AČR-I"] = {"completed": zim_chk, "teacher": zim_teacher}
            st.markdown("Splněno: **" + ("ANO" if zim_chk else "NE") + "**")
    
    ## Pravý sloupec – Letní semestr
    with col_right:
        st.subheader("Letní semestr")
        # Sekce: Základy STP-I
        st.markdown("### Základy STP-I")
        with st.expander("Detail hodnocení", expanded=True):
            for subj in ["Vojenské lezení", "Boj zblízka", "Teoretický test", "Zápočet"]:
                col1, col2 = st.columns([0.3, 0.3])
                with col1:
                    let_stp1_chk = st.checkbox(subj, value=current_student["subjects"]["letni"]["Základy STP-I"].get(subj, {}).get("completed", False), key="1Bc_let_STP1_" + subj)
                with col2:
                    let_stp1_teacher = st.text_input("Učitel, který zapsal", value=current_student["subjects"]["letni"]["Základy STP-I"].get(subj, {}).get("teacher", ""), key="1Bc_let_STP1_" + subj + "_teacher", max_chars=10)
                current_student["subjects"]["letni"]["Základy STP-I"][subj] = {"completed": let_stp1_chk, "teacher": let_stp1_teacher}
            cond_stp1 = all(current_student["subjects"]["letni"]["Základy STP-I"][s]["completed"] for s in ["Vojenské lezení", "Boj zblízka", "Teoretický test", "Zápočet"])
            st.markdown("Splněno: **" + ("ANO" if cond_stp1 else "NE") + "**")
        
        # Sekce: Speciální TP-I
        st.markdown("### Speciální TP-I")
        with st.expander("Detail hodnocení", expanded=True):
            for subj in ["Kurz BZ-I", "Kurz VL-I", "Kurz PSL", "STP-I", "Zápočet"]:
                col1, col2 = st.columns([0.3, 0.3])
                with col1:
                    let_spt1_chk = st.checkbox(subj, value=current_student["subjects"]["letni"]["Speciální TP-I"].get(subj, {}).get("completed", False), key="1Bc_let_SPT1_" + subj)
                with col2:
                    let_spt1_teacher = st.text_input("Učitel, který zapsal", value=current_student["subjects"]["letni"]["Speciální TP-I"].get(subj, {}).get("teacher", ""), key="1Bc_let_SPT1_" + subj + "_teacher", max_chars=10)
                current_student["subjects"]["letni"]["Speciální TP-I"][subj] = {"completed": let_spt1_chk, "teacher": let_spt1_teacher}
            cond_spt1 = all(current_student["subjects"]["letni"]["Speciální TP-I"][s]["completed"] for s in ["Kurz BZ-I", "Kurz VL-I", "Kurz PSL", "STP-I", "Zápočet"])
            st.markdown("Splněno: **" + ("ANO" if cond_spt1 else "NE") + "**")
    
    if st.button("Uložit hodnocení", key="save_1Bc_" + str(current_student.get("id_op", ""))):
        students_list = load_students()
        for i, s in enumerate(students_list):
            if s.get("id_op") == current_student.get("id_op"):
                students_list[i] = current_student
                break
        save_students(students_list)
        st.success("Hodnocení uloženo!")
        try:
            st.experimental_rerun()
        except AttributeError:
            pass

if __name__ == "__main__":
    run_student()
