import datetime
import streamlit as st

# ==========================================
# 📊 1. 資料初始化區 (後端工程師串接 API / 資料庫之專用接口)
# ==========================================
# --- K1: 會員與推播數據 ---
total_users_display = "144,864"  # 累積會員數 (字串格式，支援千分位)
new_users = 134                  # 本週新增會員數
total_push = 6478                # 總推播則數
weekly_push = 25                 # 當週推播則數

# --- K2: 金幣與店家當週指標 ---
weekly_coins = 2859610           # 臺東金幣當週發放數
redeem_coins = 1449010           # 商品兌換總金幣數 (當週兌換)
active_stores = 115              # 當週消費店家數
new_stores = 0                   # 當週簽約之特約店家數 (新增店家)
total_coins = 345069122          # 臺東金幣總發放數 (底層累積值)

# ==========================================
# ⚙️ 2. 頁面配置與 CSS 樣式表注入 (強制鎖定淺色模式與自訂樣式)
# ==========================================
st.set_page_config(
    page_title="TTPush 營運分析系統", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 注入 100% 原廠 style.css 骨架，確保雲端與本機視覺完全一致
st.markdown("""
<style>
/* 強制雲端全域淺色背景與黑字 */
.main .block-container {
    background-color: #ffffff !important;
    color: #1f2937 !important;
}

/* 1. 基礎卡片骨架定義 (落實統一的四等分張力) */
.unified-card {
    background: #ffffff !important;
    border: 1px solid rgba(0, 0, 0, 0.05) !important;
    border-radius: 16px !important;
    padding: 24px !important;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.015) !important;
    min-height: 385px !important;
    max-height: 385px !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-sizing: border-box !important;
}

/* 全域卡片滑鼠懸停 (Hover) 的輕微磁浮起效果 */
.unified-card:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.04) !important;
    border-color: rgba(0, 0, 0, 0.08) !important;
}

/* 2. 卡片內部區塊與文字排版 */
.card-section-top {
    flex: 1 !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: flex-start !important;
}

.card-section-bottom {
    flex: 1 !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: flex-end !important;
}

.card-label {
    font-size: 0.92rem !important;
    color: #6B7280 !important;
    font-weight: 600 !important;
    letter-spacing: 0.3px !important;
    margin-bottom: 12px !important;
    display: block !important;
}

/* 3. 核心數據大字重 (Hero Values) 比例優化 */
.hero-val-wrapper {
    display: flex !important;
    align-items: baseline !important;
    margin-top: 4px !important;
    margin-bottom: 12px !important;
}

.hero-value {
    font-size: 2.1rem !important;
    font-weight: 800 !important;
    color: #111827 !important;
    letter-spacing: -0.5px !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
}

.long-value {
    font-size: 1.75rem !important;
    font-weight: 800 !important;
    color: #111827 !important;
    letter-spacing: -0.3px !important;
}

.unit {
    font-size: 0.9rem !important;
    color: #9CA3AF !important;
    font-weight: 600 !important;
    margin-left: 6px !important;
}

/* 4. 分隔線 (與白底融為一體，維持中軸呼吸感) */
.divider-line-center {
    height: 1px !important;
    background: linear-gradient(to right, rgba(0,0,0,0.01), rgba(0,0,0,0.05) 20%, rgba(0,0,0,0.05) 80%, rgba(0,0,0,0.01)) !important;
    margin: 18px 0 !important;
    width: 100% !important;
}

/* 5. 通用列表條目樣式 */
.app-list-item {
    font-size: 0.98rem !important;
    color: #374151 !important;
    padding: 5px 0 !important;
    font-weight: 500 !important;
}

.data-bold {
    font-weight: 700 !important;
    color: #111827 !important;
}

/* 6. K1 專屬：新增會員成長標籤 */
.growth-tag {
    background: #E6F4EA !important;
    color: #137333 !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    padding: 4px 10px !important;
    border-radius: 6px !important;
    display: inline-block !important;
    margin-top: 2px !important;
}

/* 7. K2 & K3 專屬：底部備註文字 */
.section-note-bottom {
    font-size: 0.85rem !important;
    color: #9CA3AF !important;
    margin-top: 6px !important;
}

.section-note-top-k3 {
    font-size: 0.85rem !important;
    color: #9CA3AF !important;
    margin-top: -4px !important;
    margin-bottom: 8px !important;
}

/* 8. K3 專屬：歷年預算雙欄細緻雙色網格 */
.budget-grid {
    display: grid !important;
    grid-template-columns: repeat(2, 1fr) !important;
    gap: 10px !important;
    margin-top: 4px !important;
}

.budget-item {
    background: #F9FAFB !important;
    padding: 8px 10px !important;
    border-radius: 8px !important;
    border: 1px solid rgba(0,0,0,0.02) !important;
    display: flex !important;
    flex-direction: column !important;
    transition: background 0.2s ease !important;
}

.budget-item:hover {
    background: #F3F4F6 !important;
}

.b-year {
    font-size: 0.78rem !important;
    color: #6B7280 !important;
    font-weight: 500 !important;
}

.budget-item .val {
    font-size: 1.02rem !important;
    font-weight: 700 !important;
    color: #111827 !important;
    margin-top: 2px !important;
}

.b-unit {
    font-size: 0.72rem !important;
    color: #9CA3AF !important;
    margin-left: 2px !important;
    font-weight: 500 !important;
}

/* 9. K4 專屬：金幣到期預警清單與進階呼吸燈 */
.expire-list-container {
    display: flex !important;
    flex-direction: column !important;
    gap: 10px !important;
}

.expire-row {
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    padding: 6px 0 !important;
}

.expire-date {
    font-size: 0.95rem !important;
    color: #374151 !important;
    font-weight: 600 !important;
}

.expire-val-wrapper {
    display: flex !important;
    align-items: baseline !important;
}

.expire-number {
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    color: #DC2626 !important; /* 警示紅 */
}

.expire-unit {
    font-size: 0.75rem !important;
    color: #9CA3AF !important;
    margin-left: 3px !important;
    font-weight: 600 !important;
}

/* 🔔 K4 卡片滑鼠移入時觸發的「1.6秒金幣到期強烈預警脈衝燈」 */
.k4-card:hover {
    border-color: rgba(220, 38, 38, 0.25) !important;
    box-shadow: 0 12px 30px rgba(220, 38, 38, 0.06) !important;
    animation: alert-pulse 1.6s infinite ease-in-out !important;
}

@keyframes alert-pulse {
    0% { background-color: #ffffff; }
    50% { background-color: rgba(254, 242, 242, 0.6); }
    100% { background-color: #ffffff; }
}

/* 10. K4 專屬：營運備註縮排清單 */
.ops-notes {
    list-style: none !important;
    padding: 0 !important;
    margin: 4px 0 0 0 !important;
}

.ops-notes li {
    font-size: 0.86rem !important;
    color: #4B5563 !important;
    margin-bottom: 6px !important;
    line-height: 1.4 !important;
    display: flex !important;
    align-items: center !important;
}

.note-tag {
    background: #F3F4F6 !important;
    color: #4B5563 !important;
    font-size: 0.75rem !important;
    font-weight: 700 !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
    margin-right: 8px !important;
    white-space: nowrap !important;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🏹 4. 主頁面標題與【高階輕量化無邊框】動態日期控制列
# ==========================================
st.title("TTPush 週營運數據統計分析")

# 初始化全域日期狀態 (固定為定案之時間文字顯示)
date_display_text = "2026/05/01 — 2026/05/19"

# 🎨 前端 CSS Hack：完全精準復原一體化全圓角輕量綠膠囊
st.markdown(f"""
    <style>
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
            background: #E6F4EA !important;
            border: 1px solid rgba(4, 120, 87, 0.15) !important;
            border-radius: 30px !important;
            box-shadow: 0 4px 15px rgba(4, 120, 87, 0.03) !important;
            padding-left: 22px !important;
            padding-right: 22px !important;
            transition: all 0.2s ease-in-out !important;
            box-sizing: border-box !important;
        }}
        div[data-testid="stDateInput"]:hover {{
            border-color: rgba(4, 120, 87, 0.4) !important;
            box-shadow: 0 6px 20px rgba(4, 120, 87, 0.08) !important;
            transform: translateY(-1px) !important;
        }}
        div[data-testid="stDateInput"] > label {{ display: none !important; }}
        div[data-testid="stDateInput"] > div:first-child {{ background: transparent !important; border: none !important; box-shadow: none !important; width: 100% !important; }}
        div[data-testid="stDateInput"] div[data-baseweb="input"] {{ background: transparent !important; border: none !important; box-shadow: none !important; }}
        div[data-testid="stDateInput"] input {{ opacity: 0 !important; cursor: pointer !important; height: 46px !important; width: 100% !important; position: absolute !important; top: 0 !important; left: 0 !important; z-index: 5 !important; }}
        div[data-testid="stDateInput"]::before {{
            content: "📅 營運週報統計區間： {date_display_text}" !important;
            position: absolute !important; top: 0 !important; left: 0 !important; width: 100% !important; height: 100% !important;
            display: flex !important; align-items: center !important; justify-content: center !important;
            font-family: sans-serif !important; color: #1F2937 !important; font-size: 1.05rem !important; font-weight: 700 !important; z-index: 1 !important; pointer-events: none !important; box-sizing: border-box !important; white-space: nowrap !important;
        }}
        div[data-testid="stDateInput"] > div[role="dialog"] {{ width: 330px !important; }}
    </style>
""", unsafe_allow_html=True)

# 觸發器渲染
st.date_input("統計區間觸發器", value=(datetime.date(2026, 5, 1), datetime.date(2026, 5, 19)), label_visibility="collapsed")

# 定義響應式四欄位網格比例
k1, k2, k3, k4 = st.columns([1, 1, 1.1, 1.1])

# ==========================================
# 💎 5. 四大指標卡片 HTML 結構原汁原味渲染
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
            <div class="growth-tag">▲ 本週新增 +{users} 人</div>
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

# --- K4: 到期與備註 ---
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
