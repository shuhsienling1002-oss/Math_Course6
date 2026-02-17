import streamlit as st
import random

# ==========================================
# 1. 介面設定
# ==========================================
st.set_page_config(page_title="整數運算大師", page_icon="±", layout="centered")

st.markdown("""
<style>
    .stApp { background-color: #f0f4f8; color: #102a43; }
    
    /* 題目顯示區 (黑板風格優化) */
    .math-display {
        background: #243b53;
        color: white;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        text-align: center;
        margin-bottom: 20px;
        border: 4px solid #486581;
    }
    
    /* 加大數學公式字體 */
    .katex { font-size: 2.5em !important; }
    
    /* 提示區樣式 */
    .hint-box {
        background-color: #fff3c4;
        border-left: 5px solid #f6ad55;
        padding: 15px;
        color: #744210;
        border-radius: 5px;
        font-size: 1.1rem;
    }

    /* 按鈕樣式 */
    div.stButton > button {
        font-size: 1.3rem !important;
        font-weight: bold !important;
        padding: 12px !important;
        width: 100%;
        background-color: #334155;
        color: white;
    }
    div.stButton > button:hover {
        background-color: #475569;
        border-color: white;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 核心邏輯
# ==========================================

def get_op_symbol(op):
    if op == '*': return '\\times'
    if op == '/': return '\\div'
    return op

def to_latex(n, need_parens=False):
    """將整數轉為 LaTeX，負數自動加括號"""
    tex = str(n)
    if n < 0 and need_parens:
        return f"\\left( {tex} \\right)"
    return tex

def generate_question():
    """生成保證整數解的題目"""
    # 數字範圍 (-12 到 12，避免數字太大，專注符號)
    range_list = list(range(-12, 13))
    if 0 in range_list: range_list.remove(0) # 排除 0 作為除數的風險
    
    while True:
        # 生成 3 個數
        nums = [random.choice(range_list) for _ in range(3)]
        ops = [random.choice(['+', '-', '*', '/']) for _ in range(2)]
        
        # 強制檢查是否為整數解
        try:
            expr_str = f"({nums[0]}) {ops[0]} ({nums[1]}) {ops[1]} ({nums[2]})"
            ans = eval(expr_str)
            
            # 如果答案是整數，且運算過程中的除法也能整除
            if int(ans) == ans:
                # 額外檢查中間步驟是否整除
                if ops[0] == '/' and nums[0] % nums[1] != 0: continue
                if ops[1] == '/' and ops[0] not in ['*', '/']: # 後算除法
                    if nums[1] % nums[2] != 0: continue
                
                # 通過所有檢查，生成 LaTeX
                tex_1 = to_latex(nums[0], False)
                tex_2 = to_latex(nums[1], nums[1] < 0) # 如果是負數就加括號
                tex_3 = to_latex(nums[2], nums[2] < 0)
                
                full_tex = f"{tex_1} {get_op_symbol(ops[0])} {tex_2} {get_op_symbol(ops[1])} {tex_3}"
                
                # --- 智慧提示 (符號融合版) ---
                hint_msg = "💡 提示：先乘除、後加減。"
                hint_detail = ""
                
                # 偵測常見符號痛點
                # 1. 減負數 ( - (-x) ) -> 變加號
                if ops[0] == '-' and nums[1] < 0:
                    hint_msg = "💡 撞號了！「減掉負數」等於「加上正數」。"
                    hint_detail = f"試著把 {get_op_symbol(ops[0])} {to_latex(nums[1], True)} 變成 + {abs(nums[1])}"
                elif ops[1] == '-' and nums[2] < 0:
                    hint_msg = "💡 撞號了！「減掉負數」等於「加上正數」。"
                    hint_detail = f"試著把 {get_op_symbol(ops[1])} {to_latex(nums[2], True)} 變成 + {abs(nums[2])}"
                
                # 2. 加負數 ( + (-x) ) -> 變減號
                elif ops[0] == '+' and nums[1] < 0:
                    hint_msg = "💡 正負得負！「加上負數」其實就是「減法」。"
                    hint_detail = f"試著把 {get_op_symbol(ops[0])} {to_latex(nums[1], True)} 變成 - {abs(nums[1])}"
                
                # 3. 乘除負數
                elif (ops[0] in ['*', '/'] and (nums[0]*nums[1] < 0)) or \
                     (ops[1] in ['*', '/'] and (nums[1]*nums[2] < 0)):
                     hint_msg = "💡 乘除法口訣：正負得負，負負得正。"

                return {
                    "latex": full_tex,
                    "answer": int(ans),
                    "hint_msg": hint_msg,
                    "hint_detail": hint_detail
                }
        except ZeroDivisionError:
            continue

# ==========================================
# 3. 狀態管理
# ==========================================

force_reset = False
if 'q_int' in st.session_state:
    if 'hint_detail' not in st.session_state.q_int:
        force_reset = True

if 'q_int' not in st.session_state or force_reset:
    st.session_state.q_int = generate_question()
    st.session_state.int_feedback = None 
    st.session_state.u_ans = 0

# ==========================================
# 4. 畫面渲染
# ==========================================

def check_int_answer():
    if st.session_state.u_ans == st.session_state.q_int['answer']:
        st.session_state.int_feedback = 'correct'
    else:
        st.session_state.int_feedback = 'wrong'

def next_int_question():
    st.session_state.q_int = generate_question()
    st.session_state.int_feedback = None
    st.session_state.u_ans = 0

st.title("🔢 整數運算大師 (Integer Master)")
st.caption("目標：熟練正負數 (Signed Numbers) 的加減乘除與去括號變號。")

# 顯示題目
q = st.session_state.q_int
st.markdown('<div class="math-display">', unsafe_allow_html=True)
st.latex(q['latex'])
st.markdown('</div>', unsafe_allow_html=True)

# 提示區
with st.expander("💡 符號搞混了嗎？點我查看變號技巧"):
    st.markdown(f'<div class="hint-box">{q["hint_msg"]}</div>', unsafe_allow_html=True)
    if q['hint_detail']:
        st.latex(q['hint_detail'])

st.divider()

# 答題區
if st.session_state.int_feedback is None:
    c1, c2 = st.columns([2, 1])
    with c1:
        st.number_input("請輸入答案 (整數)", step=1, key="u_ans")
    with c2:
        st.write("") 
        st.write("") 
        st.button("送出答案", type="primary", on_click=check_int_answer)

# 結果回饋
else:
    ans = st.session_state.q_int['answer']
    
    if st.session_state.int_feedback == 'correct':
        st.success(f"✅ 答對了！答案是 {ans}")
        st.balloons()
    else:
        st.error(f"❌ 算錯囉，正確答案是： {ans}")
        st.markdown("別灰心，整數運算最容易錯的就是符號，再試一題！")
        
    st.button("➡️ 下一題", type="primary", on_click=next_int_question)
