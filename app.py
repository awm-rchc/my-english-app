import streamlit as st
import pandas as pd
import random
import time
import streamlit.components.v1 as components
from io import BytesIO
import difflib  # 用於比對字串差異

# --- 1. 頁面設定 ---
st.set_page_config(page_title="專業英文單字王", layout="centered", page_icon="🌿")

# --- 2. 瀏覽器發音函數 (GEMS 知識庫優化版) ---
def speak_word(word):
    t = time.time() # 強制重新渲染 JS
    js_code = f"""
    <div id="{t}" style="display:none;">
        <script>
        var msg = new SpeechSynthesisUtterance('{word}');
        msg.lang = 'en-US';
        msg.rate = 0.9;
        window.speechSynthesis.speak(msg);
        </script>
    </div>
    """
    components.html(js_code, height=0)

# --- 3. 差異標註函數 ---
def get_diff_html(user_input, correct_word):
    result = ""
    diff = difflib.ndiff(user_input.lower(), correct_word.lower())
    for char in diff:
        if char.startswith('  '): # 相同
            result += f"<span style='color:gray;'>{char[2:]}</span>"
        elif char.startswith('- '): # 多打
            result += f"<span style='color:#ff4b4b; background-color:#ffcccc; text-decoration:line-through;'>{char[2:]}</span>"
        elif char.startswith('+ '): # 漏打
            result += f"<b style='color:#28a745; background-color:#e6ffed; border-bottom:2px solid green;'>{char[2:]}</b>"
    return result

# --- 4. 讀取與過濾資料 (關鍵修正：排除 --- 與空行) ---
@st.cache_data
def load_data(file):
    try:
        df = pd.read_excel(file)
        # 強制標準化欄位名稱：移除空格並首字母大寫
        df.columns = [str(c).strip().capitalize() for c in df.columns]
        
        # 過濾邏輯
        df = df.dropna(how='all') # 移除全空行
        if 'Words' in df.columns:
            # 移除 Words 為空或包含分隔線 '---' 的行
            df = df[df['Words'].notna()]
            df = df[df['Words'].astype(str).str.strip() != '---']
        
        # 確保 Grouping 欄位格式正確，避免 sorted 報錯
        if 'Grouping' in df.columns:
            df['Grouping'] = df['Grouping'].fillna('未分類').astype(str).str.strip()
        else:
            st.error("❌ Excel 缺少 'Grouping' 欄位")
            return None
            
        return df
    except Exception as e:
        st.error(f"讀取失敗：{e}")
        return None

# --- 5. 初始化 Session State ---
if 'all_data' not in st.session_state:
    st.session_state.update({
        'all_data': None,
        'quiz_data': [],
        'quiz_queue': [],
        'current_idx': 0,
        'current_filename': "",
        'selected_group': "全部",
        'answer_mode': False,
        'last_result': None,
        'user_input_history': ""
    })

# --- 6. 側邊欄設定 ---
with st.sidebar:
    st.header("⚙️ 練習設定")
    mode = st.radio("練習模式", ["拼字練習", "四選一選擇題"])
    hint_type = st.radio("題目提示類型", ["中文 (Chinese)", "英文定義 (Definition)"])
    
    if st.session_state.all_data is not None:
        groups = ["全部"] + sorted(st.session_state.all_data['Grouping'].unique().tolist())
        new_group = st.selectbox("選擇單字組 (Grouping)", groups)
        
        if new_group != st.session_state.selected_group:
            st.session_state.selected_group = new_group
            filtered_df = st.session_state.all_data if new_group == "全部" else st.session_state.all_data[st.session_state.all_data['Grouping'] == new_group]
            st.session_state.quiz_data = filtered_df.to_dict('records')
            # 建立題號隊列並洗牌
            st.session_state.quiz_queue = random.sample(range(len(st.session_state.quiz_data)), len(st.session_state.quiz_data))
            st.session_state.current_idx = 0
            st.session_state.answer_mode = False
            st.rerun()

    st.divider()
    if st.button("🗑️ 清除所有進度"):
        st.session_state.clear()
        st.rerun()

# --- 7. 主介面 ---
st.title("🌿 專業英文單字練習")

uploaded_file = st.file_uploader("第一步：上傳 XLSX 單字表", type=["xlsx"])

if uploaded_file:
    if uploaded_file.name != st.session_state.current_filename:
        df = load_data(uploaded_file)
        if df is not None:
            st.session_state.all_data = df
            st.session_state.current_filename = uploaded_file.name
            st.session_state.quiz_data = df.to_dict('records')
            st.session_state.quiz_queue = random.sample(range(len(df)), len(df))
            st.session_state.current_idx = 0
            st.session_state.answer_mode = False
            st.rerun()

if st.session_state.all_data is not None:
    # 判斷是否完成所有題目
    if st.session_state.current_idx >= len(st.session_state.quiz_queue):
        st.balloons()
        st.success("🎉 本組練習已完成！")
        if st.button("🔄 重新開始本組"):
            st.session_state.quiz_queue = random.sample(range(len(st.session_state.quiz_data)), len(st.session_state.quiz_data))
            st.session_state.current_idx = 0
            st.session_state.answer_mode = False
            st.rerun()
    else:
        q_idx = st.session_state.quiz_queue[st.session_state.current_idx]
        item = st.session_state.quiz_data[q_idx]
        correct_word = str(item['Words']).strip()
        display_hint = item['Chinese'] if hint_type == "中文 (Chinese)" else item['Definition']

        st.caption(f"📍 組別：{st.session_state.selected_group} | 進度：{st.session_state.current_idx + 1}/{len(st.session_state.quiz_queue)}")
        st.progress(st.session_state.current_idx / len(st.session_state.quiz_queue))
        st.info(f"💡 **提示 ({hint_type.split()[0]}):** \n\n {display_hint}")

        if not st.session_state.answer_mode:
            if mode == "拼字練習":
                with st.form(key='spelling_form', clear_on_submit=True):
                    user_ans = st.text_input("請拼出單字：").strip()
                    if st.form_submit_button("提交答案"):
                        st.session_state.user_input_history = user_ans # 保留錯誤軌跡
                        st.session_state.answer_mode = True # 進入結果模式防止閃過
                        if user_ans.lower() == correct_word.lower():
                            st.session_state.last_result = "correct"
                            speak_word(correct_word)
                        else:
                            st.session_state.last_result = "wrong"
                            st.session_state.quiz_queue.append(q_idx) # 錯題強化邏析
                        st.rerun()
            else:
                # 四選一模式
                all_options = [str(d['Words']).strip() for d in st.session_state.quiz_data]
                others = [w for w in all_options if w.lower() != correct_word.lower()]
                distractors = random.sample(others, min(3, len(others))) if len(others) >= 3 else others
                options = random.sample([correct_word] + distractors, len([correct_word] + distractors))
                
                cols = st.columns(2)
                for i, opt in enumerate(options):
                    if cols[i%2].button(opt, use_container_width=True):
                        st.session_state.user_input_history = opt
                        st.session_state.answer_mode = True
                        if opt.lower() == correct_word.lower():
                            st.session_state.last_result = "correct"
                            speak_word(correct_word)
                        else:
                            st.session_state.last_result = "wrong"
                            st.session_state.quiz_queue.append(q_idx)
                        st.rerun()
        else:
            # 結果顯示區
            if st.session_state.last_result == "correct":
                st.success(f"✅ 正確！答案就是 **{correct_word}**")
            else:
                st.error(f"❌ 錯誤！正確答案是：**{correct_word}**")
                # 差異標註
                diff_html = get_diff_html(st.session_state.user_input_history, correct_word)
                st.markdown(f"""
                <div style="background-color:#f9f9f9; padding:15px; border-radius:10px; border:1px solid #ddd;">
                    <p style="color:#555; font-size:0.9em;">🔍 <b>核對拼字差異：</b></p>
                    <div style="font-family: monospace; font-size: 1.3em; letter-spacing: 2px;">{diff_html}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # 顯示備用提示
            other_hint = item['Definition'] if hint_type == "中文 (Chinese)" else item['Chinese']
            st.caption(f"🔍 補充提示：{other_hint}")

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🔊 聽發音", use_container_width=True):
                    speak_word(correct_word)
            with col_b:
                if st.button("下一題 ⏭️", use_container_width=True, type="primary"):
                    st.session_state.answer_mode = False
                    st.session_state.current_idx += 1
                    st.rerun()
