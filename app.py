import datetime
import streamlit as st

# ==========================================
# 1. 數據初始化 (精準對接 115年5月 統計週報真實數據)
# ==========================================
# --- K1: 會員與推播數據 ---
total_users_display = "144,864"  # 累積會員數
new_users = 134                  # 新增會員數
total_push = 6478                # 總推播則數
weekly_push = 25                 # 當週推播則數

# --- K2: 金幣與店家當週指標 ---
weekly_coins = 2859610           # 臺東金幣當週發放數
redeem_coins = 1449010           # 商品兌換總金幣數 (當週兌換)
active_stores = 115              # 當週消費店家數
new_stores = 0                   # 當週簽約之特約店家數 (新增店家)
total_coins = 345069122          # 臺東金幣總發放數 (底層累積值)

# ==========================================
# 2. 頁面配置與 CSS 注入
# ==========================================
st.set_page_config(page_title="TTPush 營運分析系統", layout="wide")

def load_css():
    try:
        with open("style.css", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"CSS 載入失敗: {e}")

load_css()

# ==========================================
# 🎛️ 3. 左側選單欄位設定 (Sidebar - 完美空檔保留)
# ==========================================
with st.sidebar:
    st.markdown("### ⚙️ 戰情室控制台")
    st.info("💡 此選單已釋放，保留給後續新規劃功能使用。")

# ==========================================
# 🏹 4. 主頁面標題與【現代輕量無邊框版】動態統計區間列
# ==========================================
st.title(" TTPush 週營運數據統計分析")

# 🌟 初始化全域日期狀態
if 'date_range' not in st.session_state:
    today = datetime.date.today()
    st.session_state.date_range = (today.replace(day=1), today)

# 🛠️ 【Bug 完美修復區】：將原本誤寫的 date_range 校正為 st.session_state.date_range
if isinstance(st.session_state.date_range, tuple) and len(st.session_state.date_range) == 2:
    start_date_str = st.session_state.date_range[0].strftime("%Y/%m/%d")
    end_date_str = st.session_state.date_range[1].strftime("%Y/%m/%d")
    date_display_text = f"{start_date_str} — {end_date_str}"
else:
    date_display_text = "2026/05/01 — 2026/05/16"

# 🌟 輕量化無邊框黑客 CSS：直接將原生 st.date_input 容器充當「放大版綠色膠囊」主體！
st.markdown(f"""
    <style>
        /* 1. 將原生日期組件外框直接改造為大氣、加厚的莫蘭迪綠底膠囊 */
        div[data-testid="stDateInput"] {{
            position: relative !important;
            display: inline-flex !important;
            align-items: center !important;
            width: auto !important;
            min-width: 440px !important;              
            height: 46px !important;               
            margin-top: 14px !important;
            margin-bottom: 28px !important;
            cursor: pointer !important;
            
            /* 🎨 去掉白底，直上放大版綠色標籤 */
            background: #E6F4EA !important;
            border: 1px solid rgba(4, 120, 87, 0.15) !important;
            border-radius: 30px !important;          /* 👈 經典流線全圓角膠囊造型 */
            box-shadow: 0 4px 15px rgba(4, 120, 87, 0.03) !important;
            padding-left: 22px !important;
            padding-right: 22px !important;
            transition: all 0.2s ease-in-out !important;
            box-sizing: border-box !important;
        }}
        
        /* 滑鼠移入放大綠色膠囊時的優雅泛光與微浮起特效 */
        div[data-testid="stDateInput"]:hover {{
            border-color: rgba(4, 120, 87, 0.4) !important;
            box-shadow: 0 6px 20px rgba(4, 120, 87, 0.08) !important;
            transform: translateY(-1px) !important;
        }}
        
        /* 2. 徹底隱形原始輸入框內容與文字殘影，保留上層點擊功能 */
        div[data-testid="stDateInput"] > label {{ display: none !important; }}
        
        /* 🛠️ 【視覺重組優化】：強制覆蓋原生白框殘影，讓其 100% 透明 */
        div[data-testid="stDateInput"] > div:first-child {{ 
            background: transparent !important; 
            border: none !important; 
            box-shadow: none !important; 
            width: 100% !important;
        }}
        div[data-testid="stDateInput"] div[data-baseweb="input"] {{ 
            background: transparent !important; 
            border: none !important; 
            box-shadow: none !important; 
        }}
        
        div[data-testid="stDateInput"] input {{ 
            opacity: 0 !important; 
            cursor: pointer !important;
            height: 46px !important;
            width: 100% !important;
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            z-index: 5 !important; /* 確保點擊區在最上層 */
        }}
        
        /* 3. 【一體化純視覺層】：利用偽元素，將文字與動態日期天衣無縫地結合在同一個膠囊內 */
        div[data-testid="stDateInput"]::before {{
            content: "📅 營運週報統計區間： {date_display_text}" !important;
            position: absolute !important;
            top: 0 !important; left: 0 !important;
            width: 100% !important; height: 100% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-family: sans-serif !important;
            
            /* 🎨 配色重校：內嵌文字使用精緻墨綠色與深灰平衡 */
            color: #1F2937 !important;
            font-size: 1.05rem !important;
            font-weight: 700 !important;
            
            z-index: 1 !important;
            pointer-events: none !important;
            box-sizing: border-box !important;
            white-space: nowrap !important;
        }}

        /* 4. 限制點擊彈出的月曆視窗寬度，維持 330px 精緻小巧外觀 */
        div[data-testid="stDateInput"] > div[role="dialog"] {{
            width: 330px !important;
        }}
    </style>
""", unsafe_allow_html=True)

# 原生日期輸入元件 (已透過一體化 CSS 徹底變身為高科技無邊框綠色大膠囊)
new_range = st.date_input(
    "統計區間觸發器",
    value=st.session_state.date_range,
    max_value=datetime.date.today(),
    label_visibility="collapsed"
)

# 監聽時間變更
if isinstance(new_range, tuple) and len(new_range) == 2:
    if new_range != st.session_state.date_range:
        st.session_state.date_range = new_range
        st.rerun()


# 定義四欄位排版
k1, k2, k3, k4 = st.columns([1, 1, 1.1, 1.1])

# ==========================================
# 5. 各卡片內容渲染 (使用 .format 避免解析錯誤)
# ==========================================

# --- K1: 會員與推播 ---
with k1:
    k1_html = """
    <div class="unified-card k1-card">
        <div class="card-section-top">
            <span class="card-label">累積會員總數</span>
            <div class="hero-val-wrapper">
                <span class="hero-value">{t_users}</span><span class="unit">人</span>
            </div>
            <div class="growth-tag" style="font-size: 0.95rem !important; padding: 6px 14px !important; font-weight: 700 !important; width: fit-content;">
                ▲ 本週新增 +{users} 人
            </div>
        </div>
        <div class="divider-line-center"></div>
        <div class="card-section-bottom">
            <span class="card-label">推播統計</span>
            <div class="app-list-item">📣 累計：<span class="data-bold">{t_push:,}</span> 則</div>
            <div class="app-list-item">🚀 本週：<span class="data-bold">{w_push}</span> 則</div>
        </div>
    </div>
    """.format(t_users=total_users_display, users=new_users, t_push=total_push, w_push=weekly_push)
    st.markdown(k1_html, unsafe_allow_html=True)

# --- K2: 金幣與店家 ---
with k2:
    k2_html = """
    <div class="unified-card k2-card">
        <div class="card-section-top">
            <span class="card-label">當週指標</span>  
            <div class="app-list-item">✨ 當週發放：<span class="data-bold">{w_c:,}</span> 枚</div>
            <div class="app-list-item">🎁 當週兌換：<span class="data-bold">{r_c:,}</span> 枚</div>
            <div class="app-list-item">🏪 消費店家：<span class="data-bold">{a_s}</span> 家</div>
            <div class="app-list-item">📈 新增店家：<span class="data-bold">{n_s}</span> 家</div>
        </div>
        <div class="divider-line-center"></div>
        <div class="card-section-bottom">
            <span class="card-label">臺東金幣總發放數</span>
            <div class="hero-val-wrapper">
                <span class="long-value">{t_c:,}</span><span class="unit">枚</span>
            </div>
            <div class="section-note-bottom">累積自 110/01/01 起算</div>
        </div>
    </div>
    """.format(w_c=weekly_coins, r_c=redeem_coins, a_s=active_stores, n_s=new_stores, t_c=total_coins)
    st.markdown(k2_html, unsafe_allow_html=True)

# --- K3: 歷年預算 ---
with k3:
    k3_html = """
    <div class="unified-card k3-card">
        <div class="card-section-top">
            <span class="card-label">臺東金幣總預算數</span>
            <div class="hero-val-wrapper">
                <span class="hero-value" style="font-size:1.85rem;">576,127,828</span><span class="unit">枚</span>
            </div>
            <div class="section-note-top-k3">累計110 至115年度預算（11-17期）</div>
        </div>
        <div class="divider-line-center"></div>
        <div class="card-section-bottom">
            <span class="card-label">📅 歷年預算明細</span>
            <div class="budget-grid">
                <div class="budget-item"><span class="b-year">110年/11+12期</span><span class="val">{0:,}</span><span class="b-unit">枚</span></div>
                <div class="budget-item"><span class="b-year">111年/13期</span><span class="val">{1:,}</span><span class="b-unit">枚</span></div>
                <div class="budget-item"><span class="b-year">112年/14期</span><span class="val">{2:,}</span><span class="b-unit">枚</span></div>
                <div class="budget-item"><span class="b-year">113年/15期</span><span class="val">{3:,}</span><span class="b-unit">枚</span></div>
                <div class="budget-item"><span class="b-year">114年/16期</span><span class="val">{4:,}</span><span class="b-unit">枚</span></div>
                <div class="budget-item"><span class="b-year">115年/17期</span><span class="val">{5:,}</span><span class="b-unit">枚</span></div>
            </div>
        </div>
    </div>
    """.format(176839060, 67113280, 66302010, 104541785, 82390693, 78941000)
    st.markdown(k3_html, unsafe_allow_html=True)

# --- K4: 到期與備註  ---
with k4:
    k4_html = """
    <div class="unified-card k4-card">
        <div class="card-section-top">
            <span class="card-label">⚠️ 金幣到期預警</span>
            <div class="expire-list-container">
                <div class="expire-row">
                    <span class="expire-date">2026/09/30 到期</span>
                    <div class="expire-val-wrapper">
                        <span class="expire-number">38,053,988</span><span class="expire-unit">枚</span>
                    </div>
                </div>
                <div class="expire-row">
                    <span class="expire-date">2027/09/30 到期</span>
                    <div class="expire-val-wrapper">
                        <span class="expire-number">14,054,808</span><span class="expire-unit">枚</span>
                    </div>
                </div>
            </div>
        </div>
        <div class="divider-line-center"></div>
        <div class="card-section-bottom">
            <span class="card-label">📢 營運備註整理</span>
            <ul class="ops-notes">
                <li><span class="note-tag">維護</span> 114/06/04 因 4.0 上線系統關閉維護</li>
                <li><span class="note-tag">封測</span> 114/06/23-27 進行 4.0 核心封測</li>
                <li><span class="note-tag">推播</span> 113/09/25-11/06 曾暫停金幣推播</li>
                <li><span class="note-tag">對象</span> 推播含所有用戶及縣民群組</li>
                <li><span class="note-tag">基準</span> 金幣統計自 110/01/01 起算</li>
            </ul>
        </div>
    </div>
    """
    st.markdown(k4_html, unsafe_allow_html=True)
