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

# Inicializace Supabase klienta
SUPABASE_URL = "https://bgtpylewilzcqfqaoixx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJndHB5bGV3aWx6Y3FmcWFvaXh4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ1NzQxNTQsImV4cCI6MjA2MDE1MDE1NH0.6NutsH1g8k0ruhpylqltrWD53HQFy-ZQjcUN-SULktM"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def load_students():
    try:
        response = supabase.table("students").select("*").execute()
        return response.data or []
    except Exception as e:
        st.error("Chyba při načítání studentů: " + str(e))
        return []

def save_student_record(student):
    try:
        response = supabase.table("students").update(student).eq("id_op", student["id_op"]).execute()
        return response.data
    except Exception as e:
        st.error("Chyba při ukládání: " + str(e))
        return None

default_structure_2Bc = {
    "zimni": {
        "Základy STP-II": {
            "Vojenské lezení": {"completed": False, "teacher": ""},
            "Boj zblízka": {"completed": False, "teacher": ""},
            "Teoretický test": {"completed": False, "teacher": ""},
            "Zápočet": {"completed": False, "teacher": ""}
        }
    },
    "letni": {
        "Teorie a didaktika AČR-II": {"completed": False, "teacher": ""},
        "Speciální TP-II": {
            "Kurz BZ-II": {"completed": False, "teacher": ""},
            "Kurz VL-II": {"completed": False, "teacher": ""},
            "Kurz VPL-I": {"completed": False, "teacher": ""},
            "Kurz ZP-I": {"completed": False, "teacher": ""},
            "Zápočet": {"completed": False, "teacher": ""}
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
    selected_idx = st.selectbox("Vyberte studenta", options=df.index,
                                format_func=lambda i: f"{df.loc[i, 'hodnost']} {df.loc[i, 'first_name']} {df.loc[i, 'last_name']}")
    current_student = deepcopy(cohort_students[selected_idx])
    if "subjects" not in current_student:
        current_student["subjects"] = deepcopy(default_structure_2Bc)
    else:
        for sem in default_structure_2Bc:
            current_student["subjects"].setdefault(sem, {})
            for subj, details in default_structure_2Bc[sem].items():
                current_student["subjects"][sem].setdefault(subj, deepcopy(details))
    st.markdown("## Předmětové hodnocení")
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("Zimní semestr")
        st.markdown("#### Základy STP-II")
        with st.expander("Detail hodnocení", expanded=True):
            subject_list = ["Vojenské lezení", "Boj zblízka", "Teoretický test", "Zápočet"]
            for subj in subject_list:
                col1, col2 = st.columns([0.3, 0.3])
                with col1:
                    zim_chk = st.checkbox(subj, value=current_student["subjects"]["zimni"]["Základy STP-II"].get(subj, {}).get("completed", False),
                                          key="2Bc_zim_STP2_" + subj)
                with col2:
                    zim_teacher = st.text_input("Učitel, který zapsal", value=current_student["subjects"]["zimni"]["Základy STP-II"].get(subj, {}).get("teacher", ""),
                                                 key="2Bc_zim_STP2_" + subj + "_teacher", max_chars=10)
                current_student["subjects"]["zimni"]["Základy STP-II"][subj] = {"completed": zim_chk, "teacher": zim_teacher}
            cond_zim = all(current_student["subjects"]["zimni"]["Základy STP-II"][s]["completed"] for s in subject_list)
            st.markdown("Splněno: **" + ("ANO" if cond_zim else "NE") + "**")
    
    with col_right:
        st.subheader("Letní semestr")
        st.markdown("### Teorie a didaktika AČR-II")
        with st.expander("Detail hodnocení", expanded=True):
            col1, col2 = st.columns([0.3, 0.3])
            with col1:
                let_tacr2_chk = st.checkbox("Zápočet", value=current_student["subjects"]["letni"].get("Teorie a didaktika AČR-II", {}).get("completed", False),
                                            key="2Bc_let_TACR2_Zapo")
            with col2:
                let_tacr2_teacher = st.text_input("Učitel, který zapsal", value=current_student["subjects"]["letni"].get("Teorie a didaktika AČR-II", {}).get("teacher", ""),
                                                  key="2Bc_let_TACR2_Zapo_teacher", max_chars=10)
            current_student["subjects"]["letni"]["Teorie a didaktika AČR-II"] = {"completed": let_tacr2_chk, "teacher": let_tacr2_teacher}
            st.markdown("Splněno: **" + ("ANO" if let_tacr2_chk else "NE") + "**")
        
        st.markdown("### Speciální TP-II")
        with st.expander("Detail hodnocení", expanded=True):
            subject_list2 = ["Kurz BZ-II", "Kurz VL-II", "Kurz VPL-I", "Kurz ZP-I", "Zápočet"]
            for subj in subject_list2:
                col1, col2 = st.columns([0.3, 0.3])
                with col1:
                    let_spt2_chk = st.checkbox(subj, value=current_student["subjects"]["letni"]["Speciální TP-II"].get(subj, {}).get("completed", False),
                                               key="2Bc_let_SPT2_" + subj)
                with col2:
                    let_spt2_teacher = st.text_input("Učitel, který zapsal", value=current_student["subjects"]["letni"]["Speciální TP-II"].get(subj, {}).get("teacher
