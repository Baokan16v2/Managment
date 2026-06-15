import streamlit as st
import random
import re
import os
from pypdf import PdfReader

# --- 1. CONFIGURARE ---
PDF_FILES = {
    "Capitolul 1": "Grile MANAGMENT.pdf",
    # ... adaugă restul aici
}

# --- 2. PARSARE ---
def parse_pdf_quiz(file_path):
    if not os.path.exists(file_path): return []
    try:
        reader = PdfReader(file_path)
        text = "\n".join([page.extract_text() for page in reader.pages])
    except: return []

    lines = text.split('\n')
    questions = []
    current_q_text, current_options, correct_indices = [], [], []
    state = "question" 
    
    # Regex actualizat pentru a detecta @ la început sau oriunde în variantă
    opt_pattern = re.compile(r'^(@?)([a-zA-Z])\)\s*(.*)')

    for line in lines:
        line = line.strip()
        if not line or line.lower().startswith(("capitolul", "grile")): continue

        opt_match = opt_pattern.match(line)
        if opt_match:
            state = "options"
            # Verificăm dacă @ este la începutul liniei sau în interiorul textului
            is_correct = bool(opt_match.group(1) == '@') or '@' in opt_match.group(3)
            opt_text = opt_match.group(3).replace('@', '').strip()
            
            current_options.append(opt_text)
            if is_correct: correct_indices.append(len(current_options) - 1)
        elif state == "options" and (line[0].isupper() or line[0].isdigit()):
            # Salvează întrebarea anterioară
            questions.append({"text": " ".join(current_q_text), "options": current_options, "correct_indices": correct_indices})
            current_q_text, current_options, correct_indices = [line], [], []
            state = "question"
        else:
            current_q_text.append(line)
            
    if current_q_text and current_options:
        questions.append({"text": " ".join(current_q_text), "options": current_options, "correct_indices": correct_indices})
    return questions

# --- 3. LOGICA PRINCIPALĂ ---
def main():
    st.set_page_config(page_title="Quiz", layout="wide")
    
    with st.sidebar:
        selected_chapter = st.selectbox("Alege Capitolul:", list(PDF_FILES.keys()))
        
        # --- NOU: SELECTARE MOD AFIȘARE ---
        mode = st.radio("Mod vizualizare:", ["Toate întrebările", "Seturi de 30 întrebări"])
        
        if 'questions' not in st.session_state or st.session_state.get('last_chapter') != selected_chapter:
            st.session_state.questions = parse_pdf_quiz(PDF_FILES[selected_chapter])
            st.session_state.last_chapter = selected_chapter
            st.session_state.verified_questions = set()
            st.session_state.correct_answers = set()
            random.shuffle(st.session_state.questions)

    # Logica de împărțire pe pagini
    all_qs = st.session_state.questions
    if mode == "Seturi de 30 întrebări":
        page_num = st.number_input("Pagina testului:", min_value=1, max_value=(len(all_qs)//30)+1)
        start_idx = (page_num - 1) * 30
        end_idx = start_idx + 30
        subset_questions = all_qs[start_idx:end_idx]
    else:
        subset_questions = all_qs

    st.title(f"Test: {selected_chapter}")

    for i, q in enumerate(subset_questions):
        # Calculăm indexul real în lista totală (pentru a păstra starea corectă)
        real_idx = ( (page_num - 1) * 30 + i ) if mode == "Seturi de 30 întrebări" else i
        
        st.markdown(f"#### {real_idx+1}. {q['text']}")
        selected = [idx for idx, opt in enumerate(q['options']) if st.checkbox(opt, key=f"q{real_idx}_{idx}", disabled=real_idx in st.session_state.verified_questions)]
        
        if real_idx not in st.session_state.verified_questions:
            if st.button(f"Verifică {real_idx+1}", key=f"b{real_idx}"):
                st.session_state.verified_questions.add(real_idx)
                if sorted(selected) == sorted(q['correct_indices']): st.session_state.correct_answers.add(real_idx)
                st.rerun()
        elif real_idx in st.session_state.verified_questions:
            if sorted(selected) == sorted(q['correct_indices']): st.success("Corect!")
            else: st.error(f"Greșit. Corect era: {[q['options'][i] for i in q['correct_indices']]}")

if __name__ == "__main__":
    main()