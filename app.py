import streamlit as st
import random
import math
from fractions import Fraction
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from itertools import combinations

# ==========================================
# 1. 配置與 CSS (Dynamic Edition)
# ==========================================
st.set_page_config(
    page_title="分數拼湊 v4.3", 
    page_icon="🧩", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    /* 全局背景 */
    .stApp { background-color: #1e1e2e; color: #ffffff; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 儀表板 */
    .dashboard-container {
        background: #313244;
        border-radius: 12px;
        padding: 16px;
        border: 2px solid #585b70;
        margin-bottom: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.4);
    }
    
    /* 算式區 */
    .equation-box {
        background: #11111b;
        color: #f9e2af;
        font-family: 'Courier New', monospace;
        padding: 12px;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 12px;
        border: 1px solid #45475a;
        font-size: 1.2rem;
        font-weight: bold;
    }

    /* 圓餅圖 */
    .fraction-visual-container {
        display: flex; gap: 4px; align-items: center; justify-content: center;
        margin-bottom: 6px; flex-wrap: wrap;
    }
    .pie-chart {
        width: 32px; height: 32px; border-radius: 50%;
        background: conic-gradient(#89b4fa var(--p), #45475a 0);
        border: 2px solid #cba6f7; flex-shrink: 0;
    }
    .pie-full { background: #89b4fa; border-color: #f9e2af; }
    .pie-negative { background: conic-gradient(#f38ba8 var(--p), #45475a 0); border-color: #f38ba8; }
    .pie-full-negative { background: #f38ba8; border-color: #eba0ac; }

    /* 按鈕樣式 */
    div.stButton > button {
        background-color: #cba6f7 !important; 
        color: #11111b !important;
        border-radius: 10px !important; 
        font-size: 22px !important;
        font-weight: 800 !important; 
        padding: 14px 0 !important; 
        width: 100%;
        border: 2px solid transparent !important;
        transition: transform 0.1s;
    }
    div.stButton > button:active { transform: scale(0.96); }

    /* 進度條 */
    .progress-track {
        background: #45475a; height: 28px; border-radius: 14px;
        position: relative; overflow: hidden; margin-top: 12px;
        border: 1px solid #585b70;
    }
    .progress-fill { height: 100%; transition: width 0.5s ease; background: linear-gradient(90deg, #89b4fa, #b4befe); }
    .fill-warning { background: linear-gradient(90deg, #f9e2af, #fab387); }
    .fill-danger { background: linear-gradient(90deg, #f38ba8, #eba0ac); }
    .target-line { position: absolute; top: 0; bottom: 0; width: 4px; background: #a6e3a1; z-index: 10; box-shadow: 0 0 10px #a6e3a1; }
    
    /* 狀態標籤 */
    .status-badge {
        display: inline-block; padding: 6px 10px; border-radius: 6px;
        font-size: 0.9rem; font-weight: bold; margin-bottom: 10px;
    }
    .status-ok { background: #1e3a23; color: #a6e3a1; border: 1px solid #a6e3a1; }
    .status-dead { background: #3a1e26; color: #f38ba8; border: 1px solid #f38ba8; }

    .dash-label { color: #bac2de; font-size: 1rem; font-weight: bold; margin-bottom: 4px; }
    .dash-value { font-size: 2rem; font-weight: 900; text-shadow: 0 2px 4px rgba(0,0,0,0.5); }
    
    /* 訊息框 */
    .msg-box {
        padding: 12px 16px; border-radius: 8px; margin-bottom: 16px;
        font-weight: bold; font-size: 1rem; display: flex; align-items: center;
    }
    .msg-info { background-color: rgba(137, 180, 250, 0.2); color: #89b4fa; border: 1px solid #89b4fa; }
    .msg-success { background-color: rgba(166, 227, 161, 0.2); color: #a6e3a1; border: 1px solid #a6e3a1; }
    .msg-error { background-color: rgba(243, 139, 168, 0.2); color: #f38ba8; border: 1px solid #f38ba8; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 數據模型
# ==========================================

@dataclass
class Card:
    numerator: int
    denominator: int
    id: str = field(default_factory=lambda: str(random.randint(10000, 99999)))

    @property
    def value(self) -> Fraction:
        return Fraction(self.numerator, self.denominator)

    def get_visual_html(self) -> str:
        val = self.value
        abs_val = abs(val)
        integer_part = int(abs_val)
        fraction_part = abs_val - integer_part
        
        is_neg = val < 0
        pie_class = "pie-negative" if is_neg else "pie-chart"
        full_class = "pie-full-negative" if is_neg else "pie-full"
        
        html_content = ""
        # 顯示最多 3 個滿圓，避免手機版面爆掉
        display_integers = min(integer_part, 3) 
        for _ in range(display_integers):
            html_content += f'<div class="pie-chart {full_class}" style="--p: 100%;"></div>'
        if integer_part > 3:
            html_content += '<span style="font-size:16px; color:#f9e2af; font-weight:bold;">+..</span>'
        if fraction_part > 0:
            percent = float(fraction_part) * 100
            html_content += f'<div class="{pie_class}" style="--p: {percent}%;"></div>'

        return f'<div class="fraction-visual-container">{html_content}</div>'

# ==========================================
# 3. 核心引擎 (Dynamic Targets)
# ==========================================

class GameEngine:
    @staticmethod
    def init_state():
        if 'level' not in st.session_state or 'game_status' not in st.session_state:
            st.session_state.level = 1
            GameEngine.start_level(1)

    @staticmethod
    def start_level(level: int):
        st.session_state.level = level
        target, start_val, hand, title = GameEngine._generate_smart_math(level)
        st.session_state.target = target
        st.session_state.current = start_val
        st.session_state.hand = hand
        st.session_state.played_history = []
        st.session_state.game_status = 'playing'
        st.session_state.level_title = title
        st.session_state.msg = "請湊出目標數值"
        st.session_state.msg_type = "info"
        st.session_state.solvable = True
        
        GameEngine.check_solvability()

    @staticmethod
    def _generate_smart_math(level: int):
        # [v4.3 Feature]: 動態目標生成
        # 透過 random.choice 讓每一局的目標都不一樣
        
        pools = {
            1: {
                'dens': [2, 4], 
                'target_pool': [Fraction(1, 1)], # 暖身固定為 1
                'count': 3, 'neg': False,
                'title': "暖身：完整的一 (Target 1)"
            },     
            2: {
                'dens': [2, 3, 6], 
                'target_pool': [Fraction(1, 1), Fraction(2, 1)], # 目標可能是 1 或 2
                'count': 3, 'neg': False,
                'title': "進階：1 與 2 的切換"
            },  
            3: {
                'dens': [2, 4, 8], 
                'target_pool': [Fraction(1, 1), Fraction(2, 1), Fraction(3, 1), Fraction(3, 2)], # 更多變化 (含1.5)
                'count': 4, 'neg': True,
                'title': "挑戰：整數與帶分數"
            },   
            4: {
                'dens': [2, 5, 10], 
                'target_pool': [Fraction(0, 1)], # 負數歸零關卡固定為 0
                'count': 4, 'neg': True,
                'title': "歸零：正負抵銷 (Target 0)"
            },  
            5: {
                'dens': [3, 4, 6], 
                'target_pool': [Fraction(1, 1), Fraction(2, 1), Fraction(1, 2)], # 混合：可能有 0.5
                'count': 5, 'neg': True,
                'title': "大師：變幻莫測"
            }    
        }
        cfg = pools.get(level, pools[5])
        
        # 隨機選取目標
        target_val = random.choice(cfg['target_pool'])
        correct_hand = []
        
        current_sum = Fraction(0, 1)
        for _ in range(cfg['count'] - 1):
            d = random.choice(cfg['dens'])
            n = random.choice([1, 2, 3])
            if cfg['neg'] and random.random() < 0.4: n = -n
            card = Card(n, d)
            correct_hand.append(card)
            current_sum += card.value
            
        needed = target_val - current_sum
        
        # 防止生成太醜的分數 (分母大於20或分子絕對值大於10)
        if needed.denominator > 20 or abs(needed.numerator) > 10:
            return GameEngine._generate_smart_math(level)
            
        last_card = Card(needed.numerator, needed.denominator)
        correct_hand.append(last_card)
        
        distractors = []
        d_count = 2
        for _ in range(d_count):
            d = random.choice(cfg['dens'])
            n = random.choice([1, 2])
            if cfg['neg'] and random.random() < 0.5: n = -n
            distractors.append(Card(n, d))
            
        hand = correct_hand + distractors
        random.shuffle(hand)
        
        return target_val, Fraction(0, 1), hand, cfg['title']

    @staticmethod
    def check_solvability():
        target = st.session_state.target
        current = st.session_state.current
        hand = st.session_state.hand
        needed = target - current
        vals = [c.value for c in hand]
        possible = False
        
        for r in range(len(vals) + 1):
            for subset in combinations(vals, r):
                if sum(subset) == needed:
                    possible = True
                    break
            if possible: break
            
        st.session_state.solvable = possible
        if not possible and st.session_state.game_status == 'playing':
            st.toast("⚠️ 此路不通！請悔棋 (Dead End)", icon="🚫")

    @staticmethod
    def play_card_callback(card_idx: int):
        hand = st.session_state.hand
        if 0 <= card_idx < len(hand):
            card = hand.pop(card_idx)
            st.session_state.current += card.value
            st.session_state.played_history.append(card)
            
            GameEngine.check_solvability()
            GameEngine._check_win_condition()

    @staticmethod
    def undo_callback():
        if st.session_state.played_history:
            card = st.session_state.played_history.pop()
            st.session_state.current -= card.value
            st.session_state.hand.append(card)
            
            st.toast("已悔棋", icon="↩️")
            st.session_state.game_status = 'playing'
            GameEngine.check_solvability()

    @staticmethod
    def _check_win_condition():
        curr = st.session_state.current
        tgt = st.session_state.target
        if curr == tgt:
            st.session_state.game_status = 'won'
            st.toast("挑戰成功！", icon="🎉")

# ==========================================
# 4. UI 渲染層
# ==========================================

def render_message_box(msg, type='info'):
    icons = {'info': 'ℹ️', 'success': '🎉', 'error': '⚠️', 'warning': '⚡'}
    icon = icons.get(type, 'ℹ️')
    html = f"""
    <div class="msg-box msg-{type}">
        <span style="margin-right:10px; font-size:1.2rem;">{icon}</span>
        <span>{msg}</span>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_dashboard(current: Fraction, target: Fraction):
    # 計算進度條最大值，需考慮目標變動
    calc_target = target if target != 0 else Fraction(1,1)
    
    # 動態調整 max_val，確保目標不會頂到最右邊
    max_val = max(calc_target * Fraction(3, 2), current * Fraction(11, 10), Fraction(2, 1))
    if max_val == 0: max_val = Fraction(1,1)

    curr_pct = float(current / max_val) * 100
    tgt_pct = float(target / max_val) * 100
    
    fill_class = "progress-fill"
    if current > target: fill_class += " fill-warning"
    status = st.session_state.get('game_status', 'playing')
    if status == 'lost': fill_class += " fill-danger"

    solvable = st.session_state.get('solvable', True)
    status_html = ""
    if not solvable and status == 'playing':
        status_html = '<div class="status-badge status-dead">⚠️ 死局 (Dead End)</div>'
    else:
        status_html = '<div class="status-badge status-ok">✅ 路徑通暢 (Solvable)</div>'

    html = f"""
<div class="dashboard-container">
    {status_html}
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
        <div style="text-align:center; width:45%;">
            <div class="dash-label">🎯 目標 (Target)</div>
            <div class="dash-value" style="color:#a6e3a1;">
                {target}
            </div>
        </div>
        <div style="font-size:1.5rem; color:#585b70; font-weight:900;">VS</div>
        <div style="text-align:center; width:45%;">
            <div class="dash-label">⚗️ 當前 (Current)</div>
            <div class="dash-value" style="color:#89b4fa;">
                {current}
            </div>
        </div>
    </div>
    <div class="progress-track">
        <div class="target-line" style="left: {tgt_pct}%;"></div>
        <div class="{fill_class}" style="width: {max(0, min(curr_pct, 100))}%;"></div>
    </div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)

def render_equation_log():
    history = st.session_state.played_history
    if not history:
        eq_text = "0 (起點)"
    else:
        parts = []
        for c in history:
            val_str = f"{c.numerator}/{c.denominator}"
            if c.numerator < 0: val_str = f"({val_str})"
            parts.append(val_str)
        eq_text = " + ".join(parts) + f" = {st.session_state.current}"
    
    st.markdown(f'<div class="equation-box">{eq_text}</div>', unsafe_allow_html=True)

# ==========================================
# 5. 主程式
# ==========================================

GameEngine.init_state()

st.markdown(f"#### 🧩 Lv.{st.session_state.level} {st.session_state.level_title}")

render_message_box(st.session_state.msg, st.session_state.msg_type)

render_dashboard(st.session_state.current, st.session_state.target)
render_equation_log()

if st.session_state.game_status == 'playing':
    hand = st.session_state.hand
    if not hand:
        render_message_box("手牌耗盡！請重試", "error")
        if st.button("🔄 重試", use_container_width=True):
            GameEngine.start_level(st.session_state.level)
            st.rerun()
    else:
        cols = st.columns(2)
        for i, card in enumerate(hand):
            with cols[i % 2]:
                st.markdown(card.get_visual_html(), unsafe_allow_html=True)
                n, d = card.numerator, card.denominator
                label = f"{n}/{d}"
                if abs(n) >= d:
                    whole = int(n/d)
                    rem = abs(n) % d
                    label = f"{whole}" if rem == 0 else f"{whole} {rem}/{d}"

                st.button(
                    label, 
                    key=f"btn_{card.id}", 
                    on_click=GameEngine.play_card_callback, 
                    args=(i,),
                    use_container_width=True
                )

    st.markdown("---")
    # 悔棋按鈕全寬 (無提示)
    st.button("↩️ 悔棋 (Undo)", on_click=GameEngine.undo_callback, use_container_width=True)

else:
    st.markdown("---")
    if st.session_state.game_status == 'won':
        st.balloons()
        if st.button("🚀 下一關", type="primary", use_container_width=True):
            GameEngine.start_level(st.session_state.level + 1)
            st.rerun()
        if st.button("🔄 重玩本關", use_container_width=True):
            GameEngine.start_level(st.session_state.level)
            st.rerun()
    else:
        if st.button("🔄 再試一次", type="primary", use_container_width=True):
            GameEngine.start_level(st.session_state.level)
            st.rerun()
