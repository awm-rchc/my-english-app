import streamlit as st
import pandas as pd
import random
import streamlit.components.v1 as components
from io import BytesIO

# --- 1. 頁面設定 ---
st.set_page_config(page_title="最強英文單字王", layout="centered", page_icon="🏆")

# --- 2. 瀏覽器發音函數 (JavaScript) ---
def speak_word(word):
    # 加入隨機數確保每次觸發 JS 都能被瀏覽器偵測為新組件
    js_code = f"""
    <script>
    var msg = new SpeechSynthesisUtterance('{word}');
    msg.lang = 'en-US';
    msg.rate = 0.9; // 稍微放慢一點點，聽得更清楚
    window.speechSynthesis.speak(msg);
    </script>
    """
    components.html(js_code, height=0)

# --- 3. 讀取資料 ---
@st.cache_data
def load_data(file):
    try:
        df = pd.read_excel(file)
        df.columns = [str(c).strip().capitalize() for c in df.columns]
        return df.to_dict('records')
    except Exception as e:
        st.error(f"讀取檔案失敗：{e}")
        return []

# --- 4. 初始化 Session State ---
if 'data' not in st.session_state:
    st.session_state.data = []
    st.session_state.current_idx = 0
    st.session_state.score = 0
    st.session_state.wrong_list = []
    st.session_state.quiz_queue = []
    st.session_state.initialized = False
    st.session_state.current_filename = ""
    st.session_state.answer_mode = False 
    st.session_state.last_result = None 

# --- 5. 側邊欄設定 ---
with st.sidebar:
    st.header("⚙️ 練習設定")
    mode = st.radio("選擇模式", ["拼字練習", "四選一選擇題"])
    st.divider()
    if st.button("🗑️ 清除所有進度"):
        st.session_state.clear()
        st.rerun()

    if st.session_state.wrong_list:
        st.subheader("📥 錯題本")
        wrong_df = pd.DataFrame(st.session_state.wrong_list).drop_duplicates()
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            wrong_df.to_excel(writer, index=False)
        st.download_button("下載錯題本 (XLSX)", data=output.getvalue(), file_name="my_mistakes.xlsx")

# --- 6. 主介面 ---
st.title("🏆 英文全能練習工具")

uploaded_file = st.file_uploader("第一步：上傳你的單字表 (XLSX)", type=["xlsx"])

if uploaded_file:
    if uploaded_file.name != st.session_state.current_filename:
        loaded_data = load_data(uploaded_file)
        if loaded_data:
            st.session_state.data = loaded_data
            st.session_state.quiz_queue = random.sample(range(len(loaded_data)), len(loaded_data))
            st.session_state.current_idx = 0
            st.session_state.score = 0
            st.session_state.wrong_list = []
            st.session_state.current_filename = uploaded_file.name
            st.session_state.initialized = True
            st.session_state.answer_mode = False
            st.rerun()

    if st.session_state.current_idx >= len(st.session_state.quiz_queue):
        st.balloons()
        st.success(f"🎉 太棒了！你已完成【{st.session_state.current_filename}】！")
        st.metric("最終得分", f"{st.session_state.score} 分")
        if st.button("🔄 重新開始練習"):
            st.session_state.quiz_queue = random.sample(range(len(st.session_state.data)), len(st.session_state.data))
            st.session_state.current_idx = 0
            st.session_state.score = 0
            st.session_state.answer_mode = False
            st.rerun()
    else:
        q_idx = st.session_state.quiz_queue[st.session_state.current_idx]
        current_item = st.session_state.data[q_idx]
        correct_word = str(current_item['Word']).strip()
        definition = current_item['Definition']

        st.subheader(f"📂 當前練習：{st.session_state.current_filename}")
        progress = (st.session_state.current_idx) / len(st.session_state.quiz_queue)
        st.progress(min(progress, 1.0))
        st.caption(f"進度: {st.session_state.current_idx + 1} / {len(st.session_state.quiz_queue)} | 目前得分: {st.session_state.score}")

        st.info(f"💡 定義：{definition}")

        if not st.session_state.answer_mode:
            if mode == "拼字練習":
                with st.form(key='spelling_form', clear_on_submit=True):
                    user_ans = st.text_input("請拼出單字：").strip()
                    submitted = st.form_submit_button("提交答案")
                
                if submitted:
                    st.session_state.answer_mode = True
                    if user_ans.lower() == correct_word.lower():
                        st.session_state.last_result = "correct"
                        st.session_state.score += 1
                        speak_word(correct_word)
                    else:
                        st.session_state.last_result = "wrong"
                        st.session_state.wrong_list.append(current_item)
                        st.session_state.quiz_queue.append(q_idx)
                    st.rerun()

            else:
                all_words = [str(d['Word']).strip() for d in st.session_state.data]
                others = [w for w in all_words if w.lower() != correct_word.lower()]
                distractors = random.sample(others, min(3, len(others)))
                options = [correct_word] + distractors
                random.shuffle(options)

                st.write("請選擇正確單字：")
                cols = st.columns(2)
                for i, opt in enumerate(options):
                    if cols[i%2].button(opt, use_container_width=True):
                        st.session_state.answer_mode = True
                        if opt.lower() == correct_word.lower():
                            st.session_state.last_result = "correct"
                            st.session_state.score += 1
                            speak_word(correct_word)
                        else:
                            st.session_state.last_result = "wrong"
                            st.session_state.wrong_list.append(current_item)
                            st.session_state.quiz_queue.append(q_idx)
                        st.rerun()

        else:
            if st.session_state.last_result == "correct":
                st.success(f"✅ 正確！答案是：**{correct_word}**")
            else:
                st.error(f"❌ 錯誤！正確答案應該是：**{correct_word}**")
            
            # 手動發音按鈕
            if st.button(f"🔊 聽發音: {correct_word}", use_container_width=True):
                speak_word(correct_word)
            
            st.divider()

            if st.button("下一題 ⏭️", use_container_width=True, type="primary"):
                st.session_state.answer_mode = False
                st.session_state.current_idx += 1
                st.rerun()

else:
    st.write("👋 歡迎使用！請上傳 Excel 開始練習。")
