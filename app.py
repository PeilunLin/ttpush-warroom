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
st.set_page_config(page_title="TTPush 戰情室", layout="wide", initial_sidebar_state="collapsed")

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

def on_hidden_capsule_change():
    st.session_state.selected_period = st.session_state.capsule_hidden_key

# ==========================================
# 3. 🎛️ 左側控制台開發 (純粹工作抽屜，格式完全不動)
# ==========================================
with st.sidebar:
    st.markdown("## 🎛️ TTPush 運維控制台")
    st.caption("台東金幣大數據自動化清洗引擎 v10.1")
    st.markdown("---")
    
    nav_tab = st.radio(
        "請選擇操作情境：",
        options=["👀 戰情首頁", "🔄 週報維護", "💰 預算管理", "📞 客服紀錄"],
        horizontal=True,
        label_visibility="collapsed"
    )
    st.markdown("---")
    
    if nav_tab == "👀 戰情首頁":
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

    elif nav_tab == "🔄 週報維護":
        st.warning("⚠️ 您已進入數據維護模式，操作將直接覆寫資料庫。")
        upload_mode = st.radio("請選擇匯入管線：", options=["✨ 智慧新版雙表", "⏳ 舊版單表"], horizontal=True)
        
        if upload_mode == "✨ 智慧新版雙表":
            new_files = st.file_uploader("拖曳本週「綜合報表」與「交易紀錄」：", type=["csv", "xlsx", "xls"], accept_multiple_files=True)
            if new_files and len(new_files) > 0:
                if st.button("🚀 啟動雙表對齊與繼承計算", use_container_width=True):
                    report_df, txn_df = None, None
                    for f in new_files:
                        is_excel = f.name.endswith(('.xlsx', '.xls'))
                        if "報表" in f.name:
                            report_df = pd.read_excel(f, header=None).fillna("") if is_excel else pd.read_csv(f, header=None).fillna("")
                        elif "交易" in f.name:
                            txn_df = pd.read_excel(f).fillna("") if is_excel else pd.read_csv(f).fillna("")
                    
                    if report_df is not None and txn_df is not None:
                        try:
                            new_users, new_stores, issued, redeemed = 0, 0, 0, 0
                            exp26_parsed, exp27_parsed = None, None
                            
                            for _, row in report_df.iterrows():
                                col0 = str(row[0]).strip()
                                col1 = str(row[1]).strip()
                                if col0 == "新增會員數" and col1.isdigit(): new_users = int(col1)
                                elif col0 == "新增特約店家數" and col1.isdigit(): new_stores = int(col1)
                                elif col0 == "總金幣發放枚數" and col1.isdigit(): issued = int(col1)
                                elif col0 == "民眾使用情況" and col1.isdigit(): redeemed = int(col1)
                                
                                row_str = "||".join([str(c) for c in row])
                                if "2026/09/30" in row_str or "2026/9/30" in row_str:
                                    for c in row:
                                        clean_c = str(c).replace('枚','').replace(',','').strip()
                                        if clean_c.isdigit(): exp26_parsed = int(clean_c)
                                if "2027/09/30" in row_str or "2027/9/30" in row_str:
                                    for c in row:
                                        clean_c = str(c).replace('枚','').replace(',','').strip()
                                        if clean_c.isdigit(): exp27_parsed = int(clean_c)
                            
                            active_stores = txn_df["商家名稱"].nunique() if "商家名稱" in txn_df.columns else 0
                            
                            if "交易時間" in txn_df.columns:
                                txn_df["交易時間"] = pd.to_datetime(txn_df["交易時間"])
                                min_date, max_date = txn_df["交易時間"].min(), txn_df["交易時間"].max()
                                period_key = f"統計區間：{min_date.year - 1911}/{min_date.strftime('%m/%d')} — {max_date.year - 1911}/{max_date.strftime('%m/%d')}"
                            else:
                                period_key = "統計區間：115/05/29 — 115/06/04"
                            
                            prev_data = DATA_ENGINE.get(historical_periods_list[0] if historical_periods_list else "尚無資料", {})
                            prev_k1, prev_k2, prev_k3, prev_k4 = prev_data.get("k1_metrics", {}), prev_data.get("k2_metrics", {}), prev_data.get("k3_metrics", {}), prev_data.get("k4_metrics", {})
                            
                            DATA_ENGINE[period_key] = {
                                "k1_metrics": {
                                    "actual_total_users": int(prev_k1.get("actual_total_users", 0)) + new_users,
                                    "derived_weekly_new_users": new_users,
                                    "total_push_accumulated": int(prev_k1.get("total_push_accumulated", 6465)),
                                    "weekly_push_current": 0
                                },
                                "k2_metrics": {
                                    "weekly_coins_issued": issued,
                                    "weekly_coins_redeemed_audited": redeemed,
                                    "active_stores_count": active_stores,
                                    "new_stores_adjusted": new_stores,
                                    "total_accumulated_coins": int(prev_k2.get("total_accumulated_coins", 0)) + issued,
                                    "total_stores_accumulated": int(prev_k2.get("total_stores_accumulated", 679)) + new_stores
                                },
                                "k3_metrics": prev_k3,
                                "k4_metrics": {
                                    "expire_20260930_coins": exp26_parsed if exp26_parsed is not None else int(prev_k4.get("expire_20260930_coins", 0)),
                                    "expire_20270930_coins": exp27_parsed if exp27_parsed is not None else int(prev_k4.get("expire_20270930_coins", 0))
                                }
                            }
                            
                            with open(BAK_FILE, "w", encoding="utf-8") as bak_f: json.dump(DATA_ENGINE, bak_f, ensure_ascii=False, indent=4)
                            with open(JSON_FILE, "w", encoding="utf-8") as f: json.dump(DATA_ENGINE, f, ensure_ascii=False, indent=4)
                                
                            st.success(f"✅ 成功洗入新資料：{period_key}")
                            st.session_state.selected_period = period_key
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"解析失敗: {e}")
                    else:
                        st.warning("⚠️ 請務必「同時」上傳【報表】與【會員交易紀錄】喔！")
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

    elif nav_tab == "💰 預算管理":
        st.title("💰 局處預算管理系統")
        st.info("此區塊已與右側大數據看板解耦。未來將在這裡渲染專屬的局處預算動態表格，讓您直接在網頁上調配各單位的剩餘金幣！")

    elif nav_tab == "📞 客服紀錄":
        st.title("📞 客服陳情追蹤看板")
        st.info("此區塊已成功獨立。未來將導入 Trello 般的 Kanban 看板，讓第一線話務人員在此快速建檔追蹤異常案件！")


# ==========================================
# 4. 📺 主畫面渲染 (全新 V10.1 膠囊完美疊合版)
# ==========================================
if nav_tab in ["👀 戰情首頁", "🔄 週報維護"]:
    
  # 🌟 專屬 CSS 魔法：疊合隱形選單 + 讓側邊欄懸浮不推擠主畫面
    st.markdown("""
    <style>
    /* 1. 隱形選單完美疊合魔法 */
    section[data-testid="stMain"] div[data-testid="stSelectbox"] {
        margin-top: -60px !important; 
        opacity: 0 !important;        
        z-index: 999 !important;      
        cursor: pointer !important;
    }
    /* 2. 側邊控制台「懸浮抽屜」魔法，保證不擠壓主畫面 */
    section[data-testid="stSidebar"] {
        position: absolute !important;
        z-index: 99999 !important;
        height: 100vh !important;
        box-shadow: 5px 0 15px rgba(0,0,0,0.5); /* 加點陰影讓抽屜更有立體感 */
    }
    </style>
    """, unsafe_allow_html=True)

    # 🌟 第二層：時光機獨立層 (Title之下，K1卡片之上)
    st.markdown(f"""
    <div class="capsule-visual-container" style="margin-top: 15px; margin-bottom: 5px; position: relative;">
        <div class="morandi-static-capsule">
            {st.session_state.selected_period}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 隱形控制核心 (因為上面的 CSS，它現在會死死蓋在膠囊上)
    st.selectbox(
        "隱形控制核心",
        options=historical_periods_list,
        index=historical_periods_list.index(st.session_state.selected_period) if st.session_state.selected_period in historical_periods_list else 0,
        label_visibility="collapsed",
        key="capsule_hidden_key",
        on_change=on_hidden_capsule_change
    )
    
    # 撐開與下方卡片的呼吸間距，把被下拉選單吃掉的空間補回來
    st.markdown("<div style='margin-bottom: 35px;'></div>", unsafe_allow_html=True)

    # 🌟 第三層：資料提取與原始黃金卡片網格
    current_data = DATA_ENGINE.get(st.session_state.selected_period, {})
    k1_d = current_data.get("k1_metrics", {})
    k2_d = current_data.get("k2_metrics", {})
    k3_d = current_data.get("k3_metrics", {"b110": "176,839,060", "b111": "67,113,280", "b112": "66,302,010", "b113": "104,541,785", "b114": "82,390,693", "b115": "78,941,000"})
    k4_d = current_data.get("k4_metrics", {})

    t_users_str = f"{int(k1_d.get('actual_total_users', 0)):,}"
    w_users_str = f"{int(k1_d.get('derived_weekly_new_users', 0)):,}"
    t_push_str = f"{int(k1_d.get('total_push_accumulated', 0)):,}"
    w_push_str = f"{int(k1_d.get('weekly_push_current', 0)):,}"

    w_issued_str = f"{int(k2_d.get('weekly_coins_issued', 0)):,}"
    w_redeemed_str = f"{int(k2_d.get('weekly_coins_redeemed_audited', 0)):,}"
    t_coins_str = f"{int(k2_d.get('total_accumulated_coins', 0)):,}"
    active_stores_str = f"{int(k2_d.get('active_stores_count', 0)):,}"
    new_stores_str = f"{int(k2_d.get('new_stores_adjusted', 0)):,}"
    total_stores_str = f"{int(k2_d.get('total_stores_accumulated', 679)):,}"

    b110_val = k3_d.get('b110','176,839,060')
    b111_val = k3_d.get('b111','67,113,280')
    b112_val = k3_d.get('b112','66,302,010')
    b113_val = k3_d.get('b113','104,541,785')
    b114_val = k3_d.get('b114','82,390,693')
    b115_val = k3_d.get('b115','78,941,000')

    exp26_str = f"{int(k4_d.get('expire_20260930_coins', 0)):,}"
    exp27_str = f"{int(k4_d.get('expire_20270930_coins', 0)):,}"

    # 恢復黃金比例排版
    k1, k2, k3, k4 = st.columns([0.9, 1, 1.2, 1.2])

    with k1:
        html_k1 = (
            f'<div class="unified-card k1-card">'
                f'<div class="card-section-top">'
                    f'<span class="card-label">累積會員總數</span>'
                    f'<div class="hero-val-wrapper">'
                        f'<span class="hero-value">{t_users_str}</span><span class="unit">人</span>'
                    f'</div>'
                    f'<div class="growth-tag">▲ 本週新增 +{w_users_str} 人</div>'
                f'</div>'
                f'<div class="divider-line-center"></div>'
                f'<div class="card-section-bottom">'
                    f'<span class="card-label">臺東金幣總發放數</span>'
                    f'<div class="hero-val-wrapper">'
                        f'<span class="long-value" style="font-size: 1.8rem; font-weight: 800; line-height: 1.1;">{t_coins_str}</span><span class="unit">枚</span>'
                    f'</div>'
                    f'<div class="section-note-bottom">累積自 110/01/01 起算</div>'
                f'</div>'
            f'</div>'
        )
        st.markdown(html_k1, unsafe_allow_html=True)

    with k2:
        html_k2 = (
            f'<div class="unified-card k2-card">'
                f'<div class="card-section-top">'
                    f'<span class="card-label">當週指標</span>'
                    f'<div class="app-list-item" style="margin-top: 8px;">✨ 當週發放：<span class="data-bold">{w_issued_str}</span> 枚</div>'
                    f'<div class="app-list-item">🎁 當週兌換：<span class="data-bold">{w_redeemed_str}</span> 枚</div>'
                    f'<div class="app-list-item">💲 消費店家：<span class="data-bold">{active_stores_str}</span> 家</div>'
                    f'<div class="app-list-item">🏪 總特約店：<span class="data-bold">{total_stores_str}</span> 家</div>'
                    f'<div class="app-list-item">📈 新增店家：<span class="data-bold">+{new_stores_str}</span> 家</div>'
                f'</div>'
                f'<div class="divider-line-center"></div>'
                f'<div class="card-section-bottom">'
                    f'<span class="card-label">推播統計</span>'
                    f'<div class="app-list-item">📣 累計：<span class="data-bold">{t_push_str}</span> 則</div>'
                    f'<div class="app-list-item">🚀 本週：<span class="data-bold">{w_push_str}</span> 則</div>'
                f'</div>'
            f'</div>'
        )
        st.markdown(html_k2, unsafe_allow_html=True)

    with k3:
        html_k3 = (
            f'<div class="unified-card k3-card">'
                f'<div class="card-section-top">'
                    f'<span class="card-label">臺東金幣總預算數</span>'
                    f'<div class="hero-val-wrapper">'
                        f'<span class="hero-value">576,127,828</span><span class="unit">枚</span>'
                    f'</div>'
                    f'<div class="section-note-top-k3">累計 110至115年度預算(11-17期)</div>'
                f'</div>'
                f'<div class="divider-line-center"></div>'
                f'<div class="card-section-bottom">'
                    f'<span class="card-label">📅 歷年預算明細</span>'
                    f'<div class="budget-grid">'
                        f'<div class="budget-item"><span class="b-year">110年/11+12期</span><span class="val">{b110_val}</span><span class="b-unit">枚</span></div>'
                        f'<div class="budget-item"><span class="b-year">111年/13期</span><span class="val">{b111_val}</span><span class="b-unit">枚</span></div>'
                        f'<div class="budget-item"><span class="b-year">112年/14期</span><span class="val">{b112_val}</span><span class="b-unit">枚</span></div>'
                        f'<div class="budget-item"><span class="b-year">113年/15期</span><span class="val">{b113_val}</span><span class="b-unit">枚</span></div>'
                        f'<div class="budget-item"><span class="b-year">114年/16期</span><span class="val">{b114_val}</span><span class="b-unit">枚</span></div>'
                        f'<div class="budget-item"><span class="b-year">115年/17期</span><span class="val">{b115_val}</span><span class="b-unit">枚</span></div>'
                    f'</div>'
                f'</div>'
            f'</div>'
        )
        st.markdown(html_k3, unsafe_allow_html=True)

    with k4:
        html_k4 = (
            f'<div class="unified-card k4-card">'
                f'<div class="card-section-top">'
                    f'<span class="card-label">⚠️ 金幣到期預警</span>'
                    f'<div class="expire-list-container">'
                        f'<div class="expire-row">'
                            f'<span class="expire-date">2026/09/30 到期</span>'
                            f'<div class="expire-val-wrapper">'
                                f'<span class="expire-number">{exp26_str}</span><span class="expire-unit">枚</span>'
                            f'</div>'
                        f'</div>'
                        f'<div class="expire-row">'
                            f'<span class="expire-date">2027/09/30 到期</span>'
                            f'<div class="expire-val-wrapper">'
                                f'<span class="expire-number">{exp27_str}</span><span class="expire-unit">枚</span>'
                            f'</div>'
                        f'</div>'
                    f'</div>'
                f'</div>'
                f'<div class="divider-line-center"></div>'
                f'<div class="card-section-bottom">'
                    f'<span class="card-label">📢 營運備註整理</span>'
                    f'<ul class="ops-notes">'
                        f'<li><span class="note-tag">維護</span>114/06/04 因 4.0 上線系統關閉維護</li>'
                        f'<li><span class="note-tag">封測</span>114/06/23-27 進行 4.0 核心封測</li>'
                        f'<li><span class="note-tag">推播</span>113/09/25-11/06 暫停金幣推播</li>'
                        f'<li><span class="note-tag">對象</span>推播含所有用戶及縣民群組</li>'
                        f'<li><span class="note-tag">基準</span>金幣統計自 110/01/01 起算</li>'
                    f'</ul>'
                f'</div>'
            f'</div>'
        )
        st.markdown(html_k4, unsafe_allow_html=True)