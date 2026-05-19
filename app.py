import streamlit as st

# 1. 網頁初始配置
st.set_page_config(
    page_title="TTPush 戰情室",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. 注入定案的完整 CSS 樣式
st.markdown("""
<style>
    /* 強制全局淺色背景與黑字 */
    .main .block-container {
        background-color: #FFFFFF !important;
        color: #1E1E1E !important;
        padding-top: 2rem !important;
    }
    
    /* 標題與副標題 */
    .dashboard-title {
        color: #1E40AF !important;
        font-size: 28px !important;
        font-weight: 700 !important;
        margin-bottom: 5px !important;
    }
    .dashboard-subtitle {
        color: #6B7280 !important;
        font-size: 14px !important;
        margin-bottom: 25px !important;
    }

    /* 綠色全圓角膠囊控制列 */
    .capsule-container {
        background-color: #ECFDF5 !important;
        border: 1px solid #10B981 !important;
        border-radius: 50px !important;
        padding: 10px 25px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        margin-bottom: 30px !important;
    }
    .capsule-text {
        color: #065F46 !important;
        font-weight: 600 !important;
        font-size: 16px !important;
    }

    /* K1-K4 網格排版：強制維持橫向一條線 */
    .card-grid {
        display: grid !important;
        grid-template-columns: repeat(4, 1fr) !important;
        gap: 20px !important;
        margin-bottom: 30px !important;
    }
    
    /* 白底卡片外框 */
    .metric-card {
        background-color: #FFFFFF !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
        padding: 20px !important;
        position: relative !important;
        overflow: hidden !important;
        border: 1px solid #E5E7EB !important;
    }

    /* 藍色、粉紅色漸層科技頂條 */
    .card-stripe-blue {
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        height: 6px !important;
        background: linear-gradient(90deg, #3B82F6, #60A5FA) !important;
    }
    .card-stripe-pink {
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        height: 6px !important;
        background: linear-gradient(90deg, #EC4899, #F472B6) !important;
    }

    /* 卡片內部文字 */
    .card-label {
        color: #4B5563 !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        margin-bottom: 8px !important;
    }
    .card-value {
        color: #111827 !important;
        font-size: 32px !important;
        font-weight: 700 !important;
        margin-bottom: 4px !important;
    }
    
    /* 綠色上升與呼吸預警標籤 */
    .trend-up {
        color: #10B981 !important;
        font-size: 14px !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. 渲染標題區
st.markdown('<div class="dashboard-title">📊 TTPush 週營運數據統計分析</div>', unsafe_allow_html=True)
st.markdown('<div class="dashboard-subtitle">監控區間：2026/05/01 — 2026/05/19 | 數據來源：臺東金幣營運系統</div>', unsafe_allow_html=True)

# 4. 渲染一體化綠色膠囊控制列
st.markdown("""
<div class="capsule-container">
    <div class="capsule-text">🟢 系統目前狀態：正常營運中</div>
    <div class="capsule-text">📅 數據重新整理時間：2026-05-19 15:50</div>
</div>
""", unsafe_allow_html=True)

# 5. 渲染 K1 - K4 戰情室關鍵指標卡片
st.markdown("""
<div class="card-grid">
    <div class="metric-card">
        <div class="card-stripe-blue"></div>
        <div class="card-label">👥 累積會員總數</div>
        <div class="card-value">144,864</div>
        <div class="trend-up">▲ 本週新增 +134</div>
    </div>
    <div class="metric-card">
        <div class="card-stripe-blue"></div>
        <div class="card-label">🪙 本週金幣發放數</div>
        <div class="card-value">325,400</div>
        <div class="trend-up">▲ 較上週成長 +12.4%</div>
    </div>
    <div class="metric-card">
        <div class="card-stripe-pink"></div>
        <div class="card-label">🛍️ 本週金幣回收數</div>
        <div class="card-value">284,150</div>
        <div class="trend-up">▲ 特約商店核銷踴躍</div>
    </div>
    <div class="metric-card">
        <div class="card-stripe-pink"></div>
        <div class="card-label">📱 APP 當週活躍人次 (WAU)</div>
        <div class="card-value">42,896</div>
        <div class="trend-up">▲ 活躍度維持高點</div>
    </div>
</div>
""", unsafe_allow_html=True)
