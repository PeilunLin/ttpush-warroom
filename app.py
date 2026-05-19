import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 強制設定 Streamlit 網頁為寬螢幕模式與亮色主題
st.set_page_config(
    page_title="TTPush 戰情室",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. 終極暴力注入 CSS 樣式表（徹底解決雲端黑白、卡片變形與邊條消失問題）
st.markdown("""
<style>
    /* 強制全局背景為乾淨亮白色，字體為黑色 */
    .main .block-container {
        background-color: #FFFFFF !important;
        color: #1E1E1E !important;
        padding-top: 2rem !important;
    }
    
    /* 標題樣式調校 */
    .dashboard-title {
        color: #1E40AF !important; /* 湛藍色標題 */
        font-size: 28px !important;
        font-weight: 700 !important;
        margin-bottom: 5px !important;
    }
    .dashboard-subtitle {
        color: #6B7280 !important;
        font-size: 14px !important;
        margin-bottom: 25px !important;
    }

    /* 一體化綠色膠囊控制列 */
    .capsule-container {
        background-color: #ECFDF5 !important; /* 淡淡的綠色底 */
        border: 1px solid #10B981 !important;
        border-radius: 50px !important; /* 全圓角膠囊 */
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

    /* K1-K4 戰情室指標卡片佈局 */
    .card-grid {
        display: grid !important;
        grid-template-columns: repeat(4, 1fr) !important; /* 強制橫向平分 4 個 */
        gap: 20px !important;
        margin-bottom: 30px !important;
    }
    
    .metric-card {
        background-color: #FFFFFF !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
        padding: 20px !important;
        position: relative !important;
        overflow: hidden !important;
        border: 1px solid #E5E7EB !important;
    }

    /* 卡片頂部的科技感漸層彩帶 */
    .card-stripe-blue {
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        height: 6px !important;
        background: linear-gradient(90deg, #3B82F6, #60A5FA) !important; /* 藍色漸層 */
    }
    .card-stripe-pink {
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        height: 6px !important;
        background: linear-gradient(90deg, #EC4899, #F472B6) !important; /* 粉紅漸層 */
    }

    /* 卡片字體精細化 */
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
    
    /* 綠色呼吸預警燈與上升標籤 */
    .trend-up {
        color: #10B981 !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        display: flex !important;
        align-items: center !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. 畫面標題區
st.markdown('<div class="dashboard-title">📊 TTPush 週營運數據統計分析</div>', unsafe_allow_html=True)
st.markdown('<div class="dashboard-subtitle">監控區間：2026/05/01 — 2026/05/19 | 數據來源：臺東金幣營運系統</div>', unsafe_allow_html=True)

# 4. 渲染一體化全圓角綠色膠囊控制列
st.markdown("""
<div class="capsule-container">
    <div class="capsule-text">🟢 系統目前狀態：正常營運中</div>
    <div class="capsule-text">📅 數據重新整理時間：2026-05-19 15:50</div>
</div>
""", unsafe_allow_html=True)

# 5. 渲染 K1 - K4 戰情室關鍵指標卡片（百分之百還原本機完美排版）
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

# 6. 下方補充一個簡單漂亮的圖表（確保網頁不空洞，並正常加載套件）
st.write("---")
st.subheader("📈 當週金幣發放與回收趨勢走勢")

chart_data = pd.DataFrame({
    '日期': ['05/13', '05/14', '05/15', '05/16', '05/17', '05/18', '05/19'],
    '金幣發放量': [45000, 48000, 52000, 41000, 39000, 49000, 51400],
    '金幣回收量': [38000, 41000, 46000, 39000, 35000, 42000, 43150]
})

fig = px.line(chart_data, x='日期', y=['金幣發放量', '金幣回收量'], 
              color_discrete_sequence=['#3B82F6', '#EC4899'],
              template='plotly_white')

fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
st.plotly_chart(fig, use_container_width=True)
