import pandas as pd
import streamlit as st
import json
import os
import io
import datetime
import time

# ==========================================
# 1. 🌐 全域設定與 CSS 載入
# ==========================================
st.set_page_config(page_title="TTPush 戰情室", layout="wide", initial_sidebar_state="expanded")

if os.path.exists("style.css"):
    with open("style.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ==========================================
# 2. 🧠 資料庫雙大腦初始化
# ==========================================
JSON_FILE = "metrics_history.json"
BAK_FILE = "metrics_history.json.bak"

def load_data():
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

DATA_ENGINE = load_data()
historical_periods_list = list(DATA_ENGINE.keys()) if DATA_ENGINE else ["尚無資料"]

if "selected_period" not in st.session_state:
    st.session_state.selected_period = historical_periods_list[0] if historical_periods_list else "尚無資料"

def on_sidebar_change():
    st.session_state.selected_period = st.session_state.capsule_native_key

# ==========================================
# 3. 🎛️ 左側控制台開發 (資深 UI/UX 分頁導航架構)
# ==========================================
with st.sidebar:
    st.markdown("## 🎛️ TTPush 運維控制台")
    st.caption("台東金幣大數據自動化清洗引擎 v9.5")
    st.markdown("---")
    
    # 🌟 核心 UX 重構：使用 Radio 打造橫向切換分頁標籤
    nav_tab = st.radio(
        "請選擇操作情境：",
        options=["👀 戰情首頁", "🔄 週報維護", "💰 預算管理", "📞 客服紀錄"],
        horizontal=True,
        label_visibility="collapsed"
    )
    st.markdown("---")
    
    # 【分頁一：👀 戰情首頁】
    if nav_tab == "👀 戰情首頁":
        st.markdown("#### 📅 歷史週報快速檢視")
        st.selectbox(
            "請選擇欲調閱的營業週間：",
            options=historical_periods_list,
            index=historical_periods_list.index(st.session_state.selected_period) if st.session_state.selected_period in historical_periods_list else 0,
            key="capsule_native_key",
            on_change=on_sidebar_change,
            label_visibility="collapsed"
        )
        st.info(f"💡 目前戰情室正定錨在：\n`{st.session_state.selected_period}`")
        st.markdown("---")
        st.markdown("#### 📥 歷史數據匯出")
        
        export_records = []
        for period, data in DATA_ENGINE.items():
            row = {"統計區間": period}
            row.update(data.get("k1_metrics", {}))
            row.update(data.get("k2_metrics", {}))
            row.update(data.get("k4_metrics", {}))
            export_records.append(row)
            
        if export_records:
            df_export = pd.DataFrame(export_records)
            rename_mapping = {
                "actual_total_users": "累積會員總數", "derived_weekly_new_users": "本週新增會員",
                "total_push_accumulated": "累計推播則數", "weekly_push_current": "本週推播則數",
                "weekly_coins_issued": "當週發放金幣", "weekly_coins_redeemed_audited": "當週兌換金幣",
                "active_stores_count": "消費店家數", "new_stores_adjusted": "新增店家數",
                "total_accumulated_coins": "臺東金幣總發放數", "total_stores_accumulated": "總特約店家數",
                "expire_20260930_coins": "2026到期金幣餘額", "expire_20270930_coins": "2027到期金幣餘額"
            }
            df_export = df_export.rename(columns=rename_mapping)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_export.to_excel(writer, index=False, sheet_name='TTPush歷史數據')
            output.seek(0)
            st.download_button(
                label="📥 下載全歷史 Excel 報表", data=output,
                file_name=f"TTPush_戰情室數據匯出_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    # 【分頁二：🔄 週報維護】
    elif nav_tab == "🔄 週報維護":
        st.warning("⚠️ 您已進入數據維護模式，操作將直接覆寫資料庫。")
        upload_mode = st.radio("請選擇匯入管線：", options=["✨ 智慧新版雙表", "⏳ 舊版單表"], horizontal=True)
        
        if upload_mode == "✨ 智慧新版雙表":
            new_files = st.file_uploader("拖曳本週「綜合報表」與「交易紀錄」：", type=["csv", "xlsx", "xls"], accept_multiple_files=True)
            if new_files and len(new_files) > 0:
                if st.button("🚀 啟動雙表對齊與繼承計算", use_container_width=True):
                    st.success("✅ 檔案讀取中，請稍候...")
        else:
            uploaded_files = st.file_uploader("拖曳舊版 CSV 報表：", type=["csv"], accept_multiple_files=True)

        st.markdown("---")
        st.markdown("#### ✏️ 手動數據微調")
        with st.expander("點此展開微調面板", expanded=False):
            cur_data = DATA_ENGINE.get(st.session_state.selected_period, {})
            cur_k1, cur_k2, cur_k4 = cur_data.get("k1_metrics", {}), cur_data.get("k2_metrics", {}), cur_data.get("k4_metrics", {})
            with st.form("manual_override_form"):
                col_p1, col_p2 = st.columns(2)
                with col_p1: new_w_push = st.number_input("🚀 本週推播數", value=int(cur_k1.get("weekly_push_current", 0)), step=1)
                with col_p2: new_t_push = st.number_input("📣 累積推播數", value=int(cur_k1.get("total_push_accumulated", 0)), step=1)
                col_u1, col_u2 = st.columns(2)
                with col_u1: new_w_users = st.number_input("👤 本週新增會員", value=int(cur_k1.get("derived_weekly_new_users", 0)), step=1)
                with col_u2: new_t_users = st.number_input("👥 累積會員數", value=int(cur_k1.get("actual_total_users", 0)), step=1)
                col_s1, col_s2 = st.columns(2)
                with col_s1: new_w_stores = st.number_input("📈 本週新增店家", value=int(cur_k2.get("new_stores_adjusted", 0)), step=1)
                with col_s2: new_t_stores = st.number_input("🏪 總特約店家數", value=int(cur_k2.get("total_stores_accumulated", 0)), step=1)
                col_e1, col_e2 = st.columns(2)
                with col_e1: new_exp26 = st.number_input("⏳ 2026到期", value=int(cur_k4.get("expire_20260930_coins", 0)), step=1)
                with col_e2: new_exp27 = st.number_input("⏳ 2027到期", value=int(cur_k4.get("expire_20270930_coins", 0)), step=1)
                
                if st.form_submit_button("💾 儲存並覆寫"):
                    DATA_ENGINE[st.session_state.selected_period]["k1_metrics"]["weekly_push_current"] = new_w_push
                    DATA_ENGINE[st.session_state.selected_period]["k1_metrics"]["total_push_accumulated"] = new_t_push
                    DATA_ENGINE[st.session_state.selected_period]["k1_metrics"]["derived_weekly_new_users"] = new_w_users
                    DATA_ENGINE[st.session_state.selected_period]["k1_metrics"]["actual_total_users"] = new_t_users
                    DATA_ENGINE[st.session_state.selected_period]["k2_metrics"]["new_stores_adjusted"] = new_w_stores
                    DATA_ENGINE[st.session_state.selected_period]["k2_metrics"]["total_stores_accumulated"] = new_t_stores
                    DATA_ENGINE[st.session_state.selected_period]["k4_metrics"]["expire_20260930_coins"] = new_exp26
                    DATA_ENGINE[st.session_state.selected_period]["k4_metrics"]["expire_20270930_coins"] = new_exp27
                    with open(JSON_FILE, "w", encoding="utf-8") as f: json.dump(DATA_ENGINE, f, ensure_ascii=False, indent=4)
                    st.success("✅ 數據已更新！")
                    time.sleep(0.5)
                    st.rerun()

        st.markdown("---")
        st.markdown("#### ⚙️ 資料庫安全閘門")
        col_bak, col_rst = st.columns(2)
        with col_bak:
            if st.button("💾 手動備份", use_container_width=True):
                with open(BAK_FILE, "w", encoding="utf-8") as bak_f: json.dump(DATA_ENGINE, bak_f, ensure_ascii=False, indent=4)
                st.sidebar.success("備份完畢")
        with col_rst:
            if st.button("⏪ 一鍵還原", use_container_width=True):
                if os.path.exists(BAK_FILE):
                    with open(BAK_FILE, "r", encoding="utf-8") as bak_f: restored_data = json.load(bak_f)
                    with open(JSON_FILE, "w", encoding="utf-8") as f: json.dump(restored_data, f, ensure_ascii=False, indent=4)
                    st.rerun()

    # 【分頁三：💰 預算管理】
    elif nav_tab == "💰 預算管理":
        st.markdown("#### 💰 局處預算動態配置")
        st.caption("後台 CRUD 管線準備就緒...")

    # 【分頁四：📞 客服紀錄】
    elif nav_tab == "📞 客服紀錄":
        st.markdown("#### 📞 話務即時登記看板")
        st.caption("事件驅動監聽管線準備就緒...")


# ==========================================
# 4. 📺 主畫面渲染 (連動左側分頁動態切換)
# ==========================================
# 只有在「戰情首頁」或「週報維護」時，才顯示大數據看板
if nav_tab in ["👀 戰情首頁", "🔄 週報維護"]:
    
    st.markdown('<div class="fixed-title">TTPush 週營運資料統計分析</div>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="capsule-visual-container">
        <div class="morandi-static-capsule">
            {st.session_state.selected_period}
        </div>
    </div>
    """, unsafe_allow_html=True)

    current_data = DATA_ENGINE.get(st.session_state.selected_period, {})
    k1 = current_data.get("k1_metrics", {})
    k2 = current_data.get("k2_metrics", {})
    k4 = current_data.get("k4_metrics", {})

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="unified-card k1-card">
            <div class="card-section-top">
                <span class="card-label">累積會員總數</span>
                <div class="hero-val-wrapper">
                    <span class="hero-value">{int(k1.get('actual_total_users', 0)):,}</span><span class="unit">人</span>
                </div>
                <div class="growth-tag">⬆ 本週新增 {int(k1.get('derived_weekly_new_users', 0)):,} 人</div>
            </div>
            <div class="divider-line-center"></div>
            <div class="card-section-bottom">
                <span class="card-label">臺東金幣總發放數</span>
                <div class="hero-val-wrapper">
                    <span class="hero-value" style="font-size: 1.8rem;">{int(k2.get('total_accumulated_coins', 0)):,}</span><span class="unit">枚</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="unified-card k2-card">
            <div class="card-section-top">
                <span class="card-label">當週營運指標</span>
                <div class="app-list-item">🔹當週發放 <span class="data-bold">{int(k2.get('weekly_coins_issued', 0)):,}</span> 枚</div>
                <div class="app-list-item">🔹當週兌換 <span class="data-bold">{int(k2.get('weekly_coins_redeemed_audited', 0)):,}</span> 枚</div>
                <div class="app-list-item">🔹消費店家 <span class="data-bold">{int(k2.get('active_stores_count', 0)):,}</span> 家 / 新增 <span class="data-bold">{int(k2.get('new_stores_adjusted', 0)):,}</span> 家</div>
                <div class="app-list-item">🔹總特約店 <span class="data-bold">{int(k2.get('total_stores_accumulated', 0)):,}</span> 家</div>
            </div>
            <div class="divider-line-center"></div>
            <div class="card-section-bottom">
                <span class="card-label">累計推播總數</span>
                <div class="hero-val-wrapper">
                    <span class="long-value">{int(k1.get('total_push_accumulated', 0)):,}</span><span class="unit">則</span>
                </div>
                <span class="section-note-bottom">(本週推播 {int(k1.get('weekly_push_current', 0))} 則)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="unified-card k3-card">
            <div class="card-section-top">
                <span class="card-label">歷史預算總額</span>
                <div class="hero-val-wrapper">
                    <span class="hero-value">337,458,542</span><span class="unit">枚</span>
                </div>
                <span class="section-note-top-k3">自 110 年度累計至今</span>
            </div>
            <div class="divider-line-center"></div>
            <div class="card-section-bottom">
                <div class="budget-grid">
                    <div class="budget-item"><span class="b-year">110年</span><span class="val">54,000,000</span><span class="b-unit">枚</span></div>
                    <div class="budget-item"><span class="b-year">111年</span><span class="val">53,000,000</span><span class="b-unit">枚</span></div>
                    <div class="budget-item"><span class="b-year">112年</span><span class="val">57,280,000</span><span class="b-unit">枚</span></div>
                    <div class="budget-item"><span class="b-year">113年</span><span class="val">74,380,000</span><span class="b-unit">枚</span></div>
                    <div class="budget-item"><span class="b-year">114年</span><span class="val">98,798,542</span><span class="b-unit">枚</span></div>
                    <div class="budget-item" style="border-bottom:none;"><span class="b-year">115年</span><span class="val">-</span><span class="b-unit">待編</span></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="unified-card k4-card">
            <div class="card-section-top">
                <span class="card-label">金幣到期預警</span>
                <div class="expire-list-container">
                    <div class="expire-row">
                        <span class="expire-date">2026/09/30</span>
                        <div><span class="expire-number">{int(k4.get('expire_20260930_coins', 0)):,}</span><span class="expire-unit">枚</span></div>
                    </div>
                    <div class="expire-row">
                        <span class="expire-date">2027/09/30</span>
                        <div><span class="expire-number">{int(k4.get('expire_20270930_coins', 0)):,}</span><span class="expire-unit">枚</span></div>
                    </div>
                </div>
            </div>
            <div class="divider-line-center"></div>
            <div class="card-section-bottom">
                <span class="card-label">系統營運備註</span>
                <ul class="ops-notes">
                    <li><span class="note-tag">維護</span>06/04 02:00 資料庫升級作業</li>
                    <li><span class="note-tag">封測</span>V9.5 控制台與動態網頁上線</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

elif nav_tab == "💰 預算管理":
    st.title("💰 局處預算管理系統")
    st.info("此區塊已與右側大數據看板解耦。未來將在這裡渲染專屬的局處預算動態表格，讓您直接在網頁上調配各單位的剩餘金幣！")

elif nav_tab == "📞 客服紀錄":
    st.title("📞 客服陳情追蹤看板")
    st.info("此區塊已成功獨立。未來將導入 Trello 般的 Kanban 看板，讓第一線話務人員在此快速建檔追蹤異常案件！")
