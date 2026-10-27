import streamlit as st
import random
import time
import pandas as pd
import math

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Dyscalculia Research Lab", layout="centered")

def draw_scientific_dots(count, color, dot_radius, container_id):
    """Generates a dot array with strict collision detection to prevent overlaps."""
    dots_html = ""
    placed_dots = []  # Stores (x, y, radius)
    
    max_attempts = 1000 
    attempts = 0
    
    while len(placed_dots) < count and attempts < max_attempts:
        x = random.uniform(12, 88)
        y = random.uniform(12, 88)
        
        overlap = False
        for (px, py, pr) in placed_dots:
            distance = math.sqrt((x - px)**2 + (y - py)**2)
            if distance < (dot_radius + pr) * 1.2:
                overlap = True
                break
        
        if not overlap:
            placed_dots.append((x, y, dot_radius))
            dots_html += f'<circle cx="{x}%" cy="{y}%" r="{dot_radius}%" fill="{color}" />'
        
        attempts += 1
        
    return f'''
    <div id="{container_id}" style="background-color: #c0c0c0; border: 4px solid #333; border-radius: 15px; width: 280px; height: 280px; margin: auto;">
        <svg width="100%" height="100%">{dots_html}</svg>
    </div>
    '''

# --- SESSION STATE INITIALIZATION ---
if 'data_log' not in st.session_state: 
    st.session_state.data_log = []
if 'test_active' not in st.session_state: 
    st.session_state.test_active = False
if 'current_trial' not in st.session_state:
    st.session_state.current_trial = None

# --- 1. ENTRY SCREEN ---
if not st.session_state.test_active:
    st.title("🔬 Numerosity Screener")
    st.info("System configured: Non-overlapping dot arrays, age-adapted protocols, and real-time metric analysis.")
    
    with st.form("entry"):
        name = st.text_input("Student Name")
        age = st.slider("Age", 3, 11, 7)
        s_class = st.text_input("Class")
        
        if st.form_submit_button("Start Protocol"):
            st.session_state.user_info = {"name": name, "age": age, "class": s_class}
            st.session_state.test_active = True
            st.session_state.current_trial = None
            st.rerun()

# --- 2. THE TESTING ENGINE ---
else:
    age = st.session_state.user_info['age']
    
    # Configure parameters based on age group
    if age <= 5:
        mode, ratios, c1, c2 = "Acuity (Non-Symbolic)", [0.4, 0.5], "#006400", "#00008B"
    elif 6 <= age <= 8:
        mode, ratios, c1, c2 = "Mapping (Mixed)", [0.6, 0.7], "#000000", "DIGIT"
    else:
        mode, ratios, c1, c2 = "Precision (ANS)", [0.8, 0.9], "#000000", "#000000"

    # GENERATE OR RETRIEVE TRIAL STATE (Fixes Rerun & Timing Bugs)
    if st.session_state.current_trial is None:
        ratio = random.choice(ratios)
        n_left, n_right = 10, int(10 * ratio)
        if random.choice([True, False]): 
            n_left, n_right = n_right, n_left
        
        is_incongruent = random.choice([True, False])
        radius_l = 8 if (n_left > n_right and not is_incongruent) or (n_left < n_right and is_incongruent) else 4
        radius_r = 8 if (n_right > n_left and not is_incongruent) or (n_right < n_left and is_incongruent) else 4
        
        st.session_state.current_trial = {
            "n_left": n_left,
            "n_right": n_right,
            "is_incongruent": is_incongruent,
            "radius_l": radius_l,
            "radius_r": radius_r,
            "ratio": ratio,
            "start_time": time.time()
        }

    trial = st.session_state.current_trial

    st.write(f"### Testing: **{st.session_state.user_info['name']}** | Class: **{st.session_state.user_info['class']}** | Protocol: **{mode}**")
    st.write("---")
    
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(draw_scientific_dots(trial["n_left"], c1, trial["radius_l"], "left"), unsafe_allow_html=True)
        if st.button("LEFT has MORE", use_container_width=True):
            rt = time.time() - trial["start_time"]
            correct = 1 if trial["n_left"] > trial["n_right"] else 0
            st.session_state.data_log.append({
                **st.session_state.user_info, 
                "Correct": correct, 
                "RT": rt, 
                "Type": "Incongruent" if trial["is_incongruent"] else "Congruent", 
                "Ratio": trial["ratio"], 
                "Mode": mode
            })
            st.session_state.current_trial = None  # Clear for next trial
            st.rerun()

    with col2:
        if c2 == "DIGIT":
            st.markdown(
                f'<div style="background-color: #c0c0c0; border: 4px solid #333; border-radius: 15px; width: 280px; height: 280px; display: flex; align-items: center; justify-content: center; font-size: 110px; color: #000000; font-weight: bold; margin: auto;">{trial["n_right"]}</div>', 
                unsafe_allow_html=True
            )
        else:
            st.markdown(draw_scientific_dots(trial["n_right"], c2, trial["radius_r"], "right"), unsafe_allow_html=True)
            
        if st.button("RIGHT has MORE", use_container_width=True):
            rt = time.time() - trial["start_time"]
            correct = 1 if trial["n_right"] > trial["n_left"] else 0
            st.session_state.data_log.append({
                **st.session_state.user_info, 
                "Correct": correct, 
                "RT": rt, 
                "Type": "Incongruent" if trial["is_incongruent"] else "Congruent", 
                "Ratio": trial["ratio"], 
                "Mode": mode
            })
            st.session_state.current_trial = None  # Clear for next trial
            st.rerun()

    # --- 3. SESSION MANAGEMENT & AUTOMATED SUMMARY ---
    if len(st.session_state.data_log) > 0:
        st.write("---")
        st.write(f"**Trials Completed:** {len(st.session_state.data_log)}")
        
        df = pd.DataFrame(st.session_state.data_log)
        total_acc = df['Correct'].mean() * 100
        avg_rt = df['RT'].mean()
        
        cong_acc = df[df['Type'] == 'Congruent']['Correct'].mean() * 100 if 'Congruent' in df['Type'].values else 0
        incong_acc = df[df['Type'] == 'Incongruent']['Correct'].mean() * 100 if 'Incongruent' in df['Type'].values else 0
        drop = cong_acc - incong_acc

        st.subheader("📊 Instant Student Summary")
        m1, m2, m3 = st.columns(3)
        m1.metric("Overall Accuracy", f"{total_acc:.0f}%")
        m2.metric("Average Speed", f"{avg_rt:.2f}s")
        m3.metric("Size Interference Drop", f"{drop:.0f}%", delta_color="inverse")

        if drop > 25 or total_acc < 60:
            st.error("⚠️ Indicator Flagged: High visual interference or low accuracy observed. Potential core numerosity deficit.")
        else:
            st.success("✅ Typical Profile: Strong visual independence and consistent speed.")

        if st.button("End Test & Export Data"):
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download Research CSV", 
                csv_data, 
                f"{st.session_state.user_info['name']}_results.csv", 
                "text/csv"
            )
            st.session_state.test_active = False
            st.session_state.data_log = []
            st.session_state.current_trial = None
