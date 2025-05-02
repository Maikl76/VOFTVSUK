import streamlit as st
import pandas as pd
from supabase import create_client, Client
import datetime
from copy import deepcopy
from io import BytesIO
from streamlit.runtime.scriptrunner import RerunException, RerunData

# ===== KONFIGURACE SUPABASE =====
SUPABASE_URL = st.secrets['supabase']['supabase_url']
SUPABASE_KEY = st.secrets['supabase']['supabase_key']
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ===== POMOCNÉ FUNKCE =====
def load_students():
    try:
        resp = supabase.table('students').select('*').execute()
        return resp.data or []
    except Exception as e:
        st.error('Chyba při načítání studentů: ' + str(e))
        return []

def save_student(updated_student):
    try:
        resp = (
            supabase.table('students')
                     .update(updated_student)
                     .eq('id', updated_student['id'])
                     .execute()
        )
        return resp.data
    except Exception as e:
        st.error('Chyba při aktualizaci studenta: ' + str(e))
        return None

def insert_student(new_student):
    try:
        resp = supabase.table('students').insert(new_student).execute()
        return resp.data
    except Exception as e:
        st.error('Chyba při vkládání nového studenta: ' + str(e))
        return None

def delete_student(student_id):
    try:
        resp = supabase.table('students').delete().eq('id', student_id).execute()
        return resp.data
    except Exception as e:
        st.error('Chyba při mazání studenta: ' + str(e))
        return None

# ===== PŘIDÁNÍ STUDENTA =====
def run_add_student():
    cols = st.columns([8,1])
    cols[0].header('Přidat nového studenta')
    if cols[1].button('Aktualizovat', key='update_add'):
        raise RerunException(RerunData(st.query_params))

    with st.form('add_student_form', clear_on_submit=True):
        hodnost       = st.selectbox('Hodnost', ['--','svob.','des.','čet.','rtn. Bc.','rtm. Bc.'])
        first_name    = st.text_input('Jméno')
        last_name     = st.text_input('Příjmení')
        date_of_birth = st.date_input('Datum narození', min_value=datetime.date(1960,1,1))
        address       = st.text_input('Bydliště')
        phone         = st.text_input('Telefon')
        email         = st.text_input('Email')
        id_op         = st.text_input('ID-OP')
        id_sp         = st.text_input('ID-SP')
        note          = st.text_area('Poznámka')
        study_type    = st.selectbox('Typ studia', ['Prezenční','Kombinované'])
        cohorts       = ['1. Bc.','2. Bc.','3. Bc.','1. Mgr.','2. Mgr.']
        cohort        = st.selectbox('Ročník', cohorts)
        graduated     = st.checkbox('Absolvent')
        if graduated:
            cohort = 'Absolvent'

        if st.form_submit_button('Přidat studenta'):
            new_student = {
                'hodnost':      hodnost,
                'first_name':   first_name,
                'last_name':    last_name,
                'date_of_birth': date_of_birth.strftime('%Y-%m-%d'),
                'address':      address,
                'phone':        phone,
                'email':        email,
                'id_op':        id_op,
                'id_sp':        id_sp,
                'note':         note,
                'study_type':   study_type,
                'cohort':       cohort,
                'subjects':     {},
                'is_graduated': graduated
            }
            insert_student(new_student)
            st.success('Nový student přidán!')
            raise RerunException(RerunData(st.query_params))

# ===== ÚPRAVA STUDENTA =====
def run_edit_student():
    cols = st.columns([8,1])
    cols[0].header('Editace studenta')
    if cols[1].button('Aktualizovat', key='update_edit'):
        raise RerunException(RerunData(st.query_params))

    students = load_students()
    if not students:
        st.info('Žádní studenti nejsou k dispozici ke změně.')
        return

    cohort_map = {
        'Všichni':      None,
        'První ročník': '1. Bc.',
        'Druhý ročník': '2. Bc.',
        'Třetí ročník': '3. Bc.',
        'Čtvrtý ročník':'1. Mgr.',
        'Pátý ročník':  '2. Mgr.'
    }
    choice = st.selectbox('Filtrovat ročník', list(cohort_map.keys()), key='filter_cohort')
    if cohort_map[choice]:
        filtered = [s for s in students if s.get('cohort') == cohort_map[choice]]
    else:
        filtered = [s for s in students if s.get('cohort') != 'Absolvent']

    if not filtered:
        st.info('Žádní studenti k zobrazení.')
        return

    order = {'1. Bc.':0,'2. Bc.':1,'3. Bc.':2,'1. Mgr.':3,'2. Mgr.':4}
    filtered = sorted(
        filtered,
        key=lambda s: (order.get(s.get('cohort'), len(order)), s.get('last_name',''), s.get('first_name',''))
    )

    df = pd.DataFrame(filtered).drop(columns=['id','subjects','is_graduated'], errors='ignore')
    st.dataframe(df, use_container_width=True)

    if st.button('Export do Excelu', key='export_edit'):
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name='Studenti')
        st.download_button('Stáhnout Excel', buf.getvalue(), file_name='Editace_studenti.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', key='download_edit')

    idx = st.selectbox(
        'Vyberte studenta ke změně', list(range(len(filtered))),
        format_func=lambda i: f"{filtered[i]['hodnost']} {filtered[i]['first_name']} {filtered[i]['last_name']} ({filtered[i]['cohort']})",
        key='select_student_edit'
    )
    student = deepcopy(filtered[idx])

    with st.form('edit_student_form'):
        new_hodnost = st.selectbox('Hodnost', ['--','svob.','des.','čet.','rtn. Bc.','rtm. Bc.'], index=['--','svob.','des.','čet.','rtn. Bc.','rtm. Bc.'].index(student.get('hodnost','--')))
        new_first = st.text_input('Jméno', value=student.get('first_name',''))
        new_last  = st.text_input('Příjmení', value=student.get('last_name',''))
        dob_def   = datetime.datetime.strptime(student.get('date_of_birth','1970-01-01'), '%Y-%m-%d')
        new_dob   = st.date_input('Datum narození', value=dob_def, min_value=datetime.date(1960,1,1))
        new_addr  = st.text_input('Bydliště', value=student.get('address',''))
        new_phone = st.text_input('Telefon', value=student.get('phone',''))
        new_email = st.text_input('Email', value=student.get('email',''))
        new_id_op = st.text_input('ID-OP', value=student.get('id_op',''))
        new_id_sp = st.text_input('ID-SP', value=student.get('id_sp',''))
        new_note  = st.text_area('Poznámka', value=student.get('note',''))
        new_type  = st.selectbox('Typ studia', ['Prezenční','Kombinované'], index=['Prezenční','Kombinované'].index(student.get('study_type','Prezenční')))
        cohorts   = ['1. Bc.','2. Bc.','3. Bc.','1. Mgr.','2. Mgr.','Absolvent']
        new_cohort= st.selectbox('Ročník', cohorts, index=cohorts.index(student.get('cohort','Absolvent')))
        graduated = st.checkbox('Absolvent', value=student.get('is_graduated', False))

        if graduated:
            new_cohort = 'Absolvent'

        if st.form_submit_button('Uložit změny studenta'):
            student.update({
                'hodnost':      new_hodnost,
                'first_name':   new_first,
                'last_name':    new_last,
                'date_of_birth':new_dob.strftime('%Y-%m-%d'),
                'address':      new_addr,
                'phone':        new_phone,
                'email':        new_email,
                'id_op':        new_id_op,
                'id_sp':        new_id_sp,
                'note':         new_note,
                'study_type':   new_type,
                'cohort':       new_cohort,
                'is_graduated': graduated
            })
            save_student(student)
            st.success('Změny uloženy!')
            raise RerunException(RerunData(st.query_params))

# ===== EDITACE A MAZÁNÍ ABSOLVENTŮ =====
def run_graduates():
    cols = st.columns([8,1])
    cols[0].header('Absolventi')
    if cols[1].button('Aktualizovat', key='update_grads'):
        raise RerunException(RerunData(st.query_params))

    students = load_students()
    grads = [s for s in students if s.get('is_graduated', False)]
    if not grads:
        st.info('Žádní absolventi nejsou evidováni.')
        return

    # Zobrazení seznamu absolventů
    df = pd.DataFrame(grads).drop(columns=['id','subjects','is_graduated'], errors='ignore')
    st.dataframe(df, use_container_width=True)

    # Výběr absolventa
    idx = st.selectbox(
        'Vyberte absolventa', list(range(len(grads))),
        format_func=lambda i: f"{grads[i]['hodnost']} {grads[i]['first_name']} {grads[i]['last_name']} (Absolvent)",
        key='select_graduate'
    )
    selected = deepcopy(grads[idx])

    # Formulář pro úpravu absolventa
    with st.form('edit_graduate_form'):
        st.subheader(f"Úprava absolventa {selected['first_name']} {selected['last_name']}")
        new_hodnost = st.selectbox(
            'Hodnost', ['--','svob.','des.','čet.','rtn. Bc.','rtm. Bc.'],
            index=['--','svob.','des.','čet.','rtn. Bc.','rtm. Bc.'].index(selected.get('hodnost','--'))
        )
        new_first = st.text_input('Jméno', value=selected.get('first_name',''))
        new_last  = st.text_input('Příjmení', value=selected.get('last_name',''))
        dob_def   = datetime.datetime.strptime(selected.get('date_of_birth','1970-01-01'), '%Y-%m-%d')
        new_dob   = st.date_input('Datum narození', value=dob_def, min_value=datetime.date(1960,1,1))
        new_addr  = st.text_input('Bydliště', value=selected.get('address',''))
        new_phone = st.text_input('Telefon', value=selected.get('phone',''))
        new_email = st.text_input('Email', value=selected.get('email',''))
        new_id_op = st.text_input('ID-OP', value=selected.get('id_op',''))
        new_id_sp = st.text_input('ID-SP', value=selected.get('id_sp',''))
        new_note  = st.text_area('Poznámka', value=selected.get('note',''))
        new_type  = st.selectbox(
            'Typ studia', ['Prezenční','Kombinované'],
            index=['Prezenční','Kombinované'].index(selected.get('study_type','Prezenční'))
        )
        # Odkazujeme cohort zůstává 'Absolvent'
        st.write(f"Ročník: {selected.get('cohort','Absolvent')}")
        # Tlačítko pro uložení úprav
        if st.form_submit_button('Uložit úpravy absolventa'):
            updated = deepcopy(selected)
            updated.update({
                'hodnost':      new_hodnost,
                'first_name':   new_first,
                'last_name':    new_last,
                'date_of_birth':new_dob.strftime('%Y-%m-%d'),
                'address':      new_addr,
                'phone':        new_phone,
                'email':        new_email,
                'id_op':        new_id_op,
                'id_sp':        new_id_sp,
                'note':         new_note,
                'study_type':   new_type
            })
            save_student(updated)
            st.success('Úpravy absolventa uloženy!')
            raise RerunException(RerunData(st.query_params))

        # Možnost smazat absolventa s potvrzením
    confirm = st.checkbox(
        f"Opravdu chcete smazat absolventa {selected['first_name']} {selected['last_name']}?", key='confirm_delete'
    )
    if confirm and st.button('Potvrdit smazání absolventa', key='delete_graduate'):
        delete_student(selected['id'])
        st.success('Absolvent byl smazán.')
        raise RerunException(RerunData(st.query_params))
