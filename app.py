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

# 暴力注入 100% 原廠 style.css 內容，防止雲端加載失效與黑白走樣
st.markdown("""
<style>
/* ==========================================================================
   🎨 TTPush Dashboard 頂級視覺樣式表 (工程師對接版)
   ========================================================================== */

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

/* 2. 卡片內部區塊與文字排版微調 */
.card-section-top {
    display: flex !important;
    flex-direction: column !important;
}

.card-section-bottom {
    display: flex !important;
    flex-direction: column !important;
}

.card-label {
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    color: #6b7280 !important; /* 質感冷灰 */
    margin-bottom: 8px !important;
    display: flex !important;
    align-items: center !important;
    gap: 6px !important;
}

/* 數據核心字體與數位感微調 */
.card-main-value {
    font-size: 2.25rem !important;
    font-weight: 800 !important;
    color: #111827 !important; /* 深邃灰黑 */
    line-height: 1 !important;
    letter-spacing: -0.03em !important;
    margin-bottom: 12px !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
}

/* 3. 卡片專屬邊條視覺 (落實藍粉科技張力) */
.k1-card { border-top: 5px solid #3b82f6 !important; } /* 科技藍 */
.k2-card { border-top: 5px solid #2563eb !important; } /* 數位深藍 */
.k3-card { border-top: 5px solid #ec4899 !important; } /* 潮流粉 */
.k4-card { border-top: 5px solid #dc2626 !important; } /* 警示紅 */

/* 4. 數據清單排版引擎 (Grid & Flexbox) */
.data-row-flex {
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    padding: 8px 0 !important;
    border-bottom: 1px dashed #f3f4f6 !important;
}

.data-row-flex:last-child {
    border-bottom: none !important;
    padding-bottom: 0 !important;
}

.data-row-label {
    font-size: 0.85rem !important;
    color: #4b5563 !important;
    font-weight: 500 !important;
}

.data-row-value {
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    color: #1f2937 !important;
}

/* 綠色調、上升指標之標籤 */
.badge-trend-up {
    background-color: #ecfdf5 !important;
    color: #059669 !important;
    padding: 2px 8px !important;
    border-radius: 6px !important;
    font-size: 0.75rem !important;
    font-weight: 700 !important;
}

/* 中間垂直虛線分隔線 (K1, K2, K3 專用) */
.divider-line-center {
    width: 100% !important;
    border-top: 1px dashed #e5e7eb !important;
    margin: 16px 0 !important;
}

/* 5. 專屬元件：K4 到期金幣排版 */
.expire-list-container {
    display: flex !important;
    flex-direction: column !important;
    gap: 8px !important;
    margin-top: 4px !important;
}

.expire-row {
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    background: #fef2f2 !important; /* 極淡紅底 */
    padding: 6px 12px !important;
    border-radius: 8px !important;
}

.expire-date {
    font-size: 0.8rem !important;
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
    color: #dc2626 !important; /* 警示紅 */
}

.expire-unit {
    font-size: 0.75rem !important;
    color: #9ca3af !important;
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
    50% { background-color: rgba(254, 242, 242, 0.6); } /* 柔和警示粉紅淡出 */
    100% { background-color: #ffffff; }
}

/* 營運備註 UL 項目樣式優化 */
.ops-notes {
    margin: 0 !important;
    padding-left: 16px !important;
    font-size: 0.8rem !important;
    color: #4b5563 !important;
    line-height: 1.6 !important;
}

.ops-notes li {
    margin-bottom: 6px !important;
}

.ops-notes li:last-child {
    margin-bottom: 0 !important;
}

.note-tag {
    font-weight: 700 !important;
    color: #4f46e5 !important; /* 標籤靛藍 */
    margin-right: 4px !important;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🎬 3. 前端 UI 渲染引擎 (HTML 原生架構，確保雲端 100% 還原不走樣)
# ==========================================

# --- 頂部大標題區 ---
st.title("📊 TTPush 營運分析系統")

# --- 四等分卡片排版核心 ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="unified-card k1-card">
        <div class="card-section-top">
            <span class="card-label">👥 累積會員總數</span>
            <span class="card-main-value">{total_users_display}</span>
            <div class="data-row-flex">
                <span class="data-row-label">本週新增會員數</span>
                <span class="badge-trend-up">+{new_users} 人</span>
            </div>
        </div>
        <div class="divider-line-center"></div>
        <div class="card-section-bottom">
            <span class="card-label">📢 推播發放成效</span>
            <div class="data-row-flex">
                <span class="data-row-label">歷史累積總推播</span>
                <span class="data-row-value">{total_push:,} 則</span>
            </div>
            <div class="data-row-flex">
                <span class="data-row-label">當週推播發放數</span>
                <span class="data-row-value">{weekly_push} 則</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="unified-card k2-card">
        <div class="card-section-top">
            <span class="card-label">🪙 金幣當週指標</span>
            <span class="card-main-value">{weekly_coins:,}</span>
            <div class="data-row-flex">
                <span class="data-row-label">商品兌換總金幣數</span>
                <span class="data-row-value" style="color: #2563eb;">{redeem_coins:,} 枚</span>
            </div>
        </div>
        <div class="divider-line-center"></div>
        <div class="card-section-bottom">
            <span class="card-label">🏪 特約店家生態圈</span>
            <div class="data-row-flex">
                <span class="data-row-label">當週消費店家數</span>
                <span class="data-row-value">{active_stores} 家</span>
            </div>
            <div class="data-row-flex">
                <span class="data-row-label">當週新增特約店</span>
                <span class="data-row-value" style="color: #9ca3af;">{new_stores} 家</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="unified-card k3-card">
        <div class="card-section-top">
            <span class="card-label">📈 歷史累積發放總量</span>
            <span class="card-main-value" style="font-size: 1.85rem; padding-top: 5px; padding-bottom: 5px;">{total_coins:,}</span>
            <div class="data-row-flex" style="margin-top: 2px;">
                <span class="data-row-label">系統初始發放基石</span>
                <span class="data-row-value">110-113年累積</span>
            </div>
        </div>
        <div class="divider-line-center"></div>
        <div class="card-section-bottom">
            <span class="card-label">💡 專案核心提示</span>
            <div style="font-size: 0.82rem; color: #4b5563; line-height: 1.5; padding-top: 2px;">
                本區間數據已排除內部測試扣記帳額度，全數落實為台東縣民之真實金幣流轉規模，做為未來觀光導流與跨機關預算評估之核心基準。
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="unified-card k4-card">
        <div class="card-section-top">
            <span class="card-label">⚠️ 金幣到期預警</span>
            <div class="expire-list-container">
                <div class="expire-row">
                    <span class="expire-date">2026/09/30 到期</span>
                    <div class="expire-val-wrapper">
                        <span class="expire-number">38,053,988</span><span class=\"expire-unit\">枚</span>
                    </div>
                </div>
                <div class="expire-row">
                    <span class="expire-date">2027/09/30 到期</span>
                    <div class="expire-val-wrapper">
                        <span class="expire-number">14,054,808</span><span class=\"expire-unit\">枚</span>
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
                <li><span class="note-tag">推播</span> 113/09/25-11/06 曾進行大規模縣政推播</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)
