import pandas as pd
import streamlit as st
import json
import os
import io
import datetime
import time
from github import Github 

# ==========================================
# 1. 🌐 全域設定與 CSS 載入
# ==========================================
st.set_page_config(page_title="TTPush 戰情室", layout="wide", initial_sidebar_state="collapsed")

# 🌟 V11.8 極簡留白美學 CSS
st.markdown("""
<style>
/* 1. 移除 Streamlit 預設的側邊欄上方大片白邊 */
[data-testid="stSidebarUserContent"] {
    padding-top: 0rem !important;
}

/* 2. 懸浮置頂的標題區塊 (無邊框極簡風) */
.sidebar-header-sticky {
    position: sticky;
    top: 0px;
    background-color: #f0f2f6; 
    z-index: 999;
    padding-top: 2rem;
    padding-bottom: 1rem;
    margin-left: -1.5rem;
    margin-right: -1.5rem;
    padding-left: 1.5rem;
    padding-right: 1.5rem;
}

/* 3. 懸浮置底的版本資訊區塊 (置中極簡風) */
.sidebar-footer-sticky {
    position: sticky;
    bottom: 0px;
    background-color: #f0f2f6;
    z-index: 999;
    padding-top: 1rem;
    padding-bottom: 2rem;
    margin-left: -1.5rem;
    margin-right: -1.5rem;
    padding-left: 1.5rem;
    padding-right: 1.5rem;
    text-align: center;
}

/* 支援深色模式的背景自動切換 */
@media (prefers-color-scheme: dark) {
    .sidebar-header-sticky, .sidebar-footer-sticky {
        background-color: #262730;
    }
}
</style>
""", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CSS_PATH = os.path.join(BASE_DIR, "style.css")
if os.path.exists(CSS_PATH):
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ==========================================
# 2. 🧠 資料庫雙大腦初始化與強制排序 
# ==========================================
JSON_FILE = os.path.join(BASE_DIR, "metrics_history.json")
BAK_FILE = os.path.join(BASE_DIR, "metrics_history.json.bak")

def load_data():
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

DATA_ENGINE = load_data()

if DATA_ENGINE:
    historical_periods_list = sorted(list(DATA_ENGINE.keys()), reverse=True)
else:
    historical_periods_list = ["尚無資料"]

if "selected_period" not in st.session_state:
    st.session_state.selected_period = historical_periods_list[0] if historical_periods_list else "尚無資料"

def on_sidebar_change():
    st.session_state.selected_period = st.session_state.capsule_native_key

def on_hidden_capsule_change():
    st.session_state.selected_period = st.session_state.capsule_hidden_key

def safe_parse_int(val):
    try:
        clean_val = str(val).replace(',', '').replace('枚', '').strip()
        if not clean_val: return None
        return int(float(clean_val))
    except (ValueError, TypeError):
        return None

# ==========================================
# 3. 🎛️ 左側控制台開發 (V11.8)
# ==========================================
with st.sidebar:
    
    # --- 頂部懸浮標題 ---
    st.markdown(
        """
        <div class="sidebar-header-sticky">
            <h2 style="margin:0; font-size: 1.65rem; font-weight: 800; color: inherit; letter-spacing: -0.5px;">🎛️ TTPUSH維運控制台</h2>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    nav_tab = st.radio(
        "請選擇操作情境：",
        options=["👀 戰情首頁", "🔄 週報維護", "💰 預算管理", "📞 客服紀錄"],
        horizontal=False,
        label_visibility="collapsed"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if nav_tab == "👀 戰情首頁":
        # 完美復刻的 Info Box
        st.info(f"💡 目前戰情室正定錨在：\n\n**{st.session_state.selected_period}**")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 專屬藍色大標題
        st.markdown('<h4 style="color: #2563eb; font-weight: 800; margin-bottom: 15px;">📥 歷史數據匯出</h4>', unsafe_allow_html=True)
        
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
            
            # 主色按鈕
            st.download_button(
                label="📥 下載全歷史 Excel 報表", data=output,
                file_name=f"TTPush_戰情室數據匯出_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary"
            )

    elif nav_tab == "🔄 週報維護":
        st.success("ℹ️ **維護模式**：操作將自動連動 GitHub 雲端資料庫。")
        
        prev_data = DATA_ENGINE.get(historical_periods_list[0] if historical_periods_list else "尚無資料", {})
        prev_k1 = prev_data.get("k1_metrics", {})
        prev_k2 = prev_data.get("k2_metrics", {})
        prev_k3 = prev_data.get("k3_metrics", {})
        prev_k4 = prev_data.get("k4_metrics", {})
        
        default_raw_users = max(0, int(prev_k1.get("actual_total_users", 40627)) - 40627)

        st.markdown("### 📥 步驟一：參數設定與載入")
        
        with st.container(border=True):
            st.markdown("##### 📝 手動參數")
            col_p1, col_p2 = st.columns(2)
            with col_p1: raw_users_input = st.number_input("👤 後台會員總數", min_value=0, step=1, value=default_raw_users)
            with col_p2: new_push_input = st.number_input("🚀 本週新增推播", min_value=0, step=1, value=0)
            
            col_p3, col_p4 = st.columns(2)
            with col_p3: new_stores_input = st.number_input("📈 本週新增店家", min_value=0, step=1, value=0)
            with col_p4: wallet_adj_input = st.number_input("💰 錢包調整項", step=1, value=0, help="正值為補發/匯入，負值為扣除/回收")

        st.markdown("##### 📁 報表匯入")
        new_files = st.file_uploader("拖曳本週「綜合報表」與「交易紀錄」：", type=["csv", "xlsx", "xls"], accept_multiple_files=True, label_visibility="collapsed")
        
        if new_files and len(new_files) > 0:
            if st.button("🚀 啟動解析並產生暫存", use_container_width=True, type="primary"):
                report_df, txn_df = None, None
                for f in new_files:
                    is_excel = f.name.endswith(('.xlsx', '.xls'))
                    if "報表" in f.name:
                        report_df = pd.read_excel(f, header=None).fillna("") if is_excel else pd.read_csv(f, header=None).fillna("")
                    elif "交易" in f.name:
                        txn_df = pd.read_excel(f).fillna("") if is_excel else pd.read_csv(f).fillna("")
                
                if report_df is not None and txn_df is not None:
                    try:
                        issued, redeemed = 0, 0
                        exp26_parsed, exp27_parsed = None, None
                        
                        for _, row in report_df.iterrows():
                            col0 = str(row[0]).strip()
                            parsed_val = safe_parse_int(row[1])
                            
                            if parsed_val is not None:
                                if col0 == "總金幣發放枚數": issued = parsed_val
                                elif col0 == "民眾使用情況": redeemed = parsed_val
                            
                            row_str = "||".join([str(c) for c in row])
                            
                            is_exp26 = any(d in row_str for d in ["2026/09/30", "2026/9/30", "2026-09-30", "2026-9-30", "115/09/30", "115-09-30"])
                            is_exp27 = any(d in row_str for d in ["2027/09/30", "2027/9/30", "2027-09-30", "2027-9-30", "116/09/30", "116-09-30"])
                            
                            if is_exp26:
                                for c in row:
                                    val = safe_parse_int(c)
                                    if val is not None and val > 1000 and val != 20260930:
                                        if exp26_parsed is None or val > exp26_parsed: exp26_parsed = val
                                            
                            if is_exp27:
                                for c in row:
                                    val = safe_parse_int(c)
                                    if val is not None and val > 1000 and val != 20270930:
                                        if exp27_parsed is None or val > exp27_parsed: exp27_parsed = val
                        
                        active_stores = txn_df["商家名稱"].nunique() if "商家名稱" in txn_df.columns else 0
                        
                        if "交易時間" in txn_df.columns:
                            txn_df["交易時間"] = pd.to_datetime(txn_df["交易時間"])
                            min_date, max_date = txn_df["交易時間"].min(), txn_df["交易時間"].max()
                            period_key = f"統計區間：{min_date.year - 1911}/{min_date.strftime('%m/%d')} — {max_date.year - 1911}/{max_date.strftime('%m/%d')}"
                        else:
                            period_key = "統計區間：115/05/29 — 115/06/04"
                        
                        actual_users = raw_users_input + 40627
                        derived_new_users = actual_users - int(prev_k1.get("actual_total_users", actual_users))
                        actual_total_push = int(prev_k1.get("total_push_accumulated", 0)) + new_push_input
                        actual_total_stores = int(prev_k2.get("total_stores_accumulated", 679)) + new_stores_input
                        
                        adjusted_issued = issued + wallet_adj_input

                        DATA_ENGINE[period_key] = {
                            "k1_metrics": {
                                "actual_total_users": actual_users,
                                "derived_weekly_new_users": derived_new_users,
                                "total_push_accumulated": actual_total_push,
                                "weekly_push_current": new_push_input
                            },
                            "k2_metrics": {
                                "weekly_coins_issued": adjusted_issued,
                                "weekly_coins_redeemed_audited": redeemed,
                                "active_stores_count": active_stores,
                                "new_stores_adjusted": new_stores_input,
                                "total_accumulated_coins": int(prev_k2.get("total_accumulated_coins", 0)) + adjusted_issued,
                                "total_stores_accumulated": actual_total_stores
                            },
                            "k3_metrics": prev_k3,
                            "k4_metrics": {
                                "expire_20260930_coins": exp26_parsed if exp26_parsed is not None else int(prev_k4.get("expire_20260930_coins", 0)),
                                "expire_20270930_coins": exp27_parsed if exp27_parsed is not None else int(prev_k4.get("expire_20270930_coins", 0))
                            }
                        }
                        
                        with open(BAK_FILE, "w", encoding="utf-8") as bak_f: json.dump(DATA_ENGINE, bak_f, ensure_ascii=False, indent=4)
                        with open(JSON_FILE, "w", encoding="utf-8") as f: json.dump(DATA_ENGINE, f, ensure_ascii=False, indent=4)
                            
                        st.success(f"✅ 解析完成！請展開下方進階面板進行雲端同步。")
                        st.session_state.selected_period = period_key
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 解析失敗: {e}")
                else:
                    st.warning("⚠️ 請務必同時上傳「綜合報表」與「交易紀錄」！")

        st.markdown("---")
        st.markdown("### 🛠️ 步驟二：審核與同步")
        
        with st.expander("⚙️ 進階：手動數據微調與雲端同步", expanded=False):
            cur_data = DATA_ENGINE.get(st.session_state.selected_period, {})
            cur_k1, cur_k2, cur_k4 = cur_data.get("k1_metrics", {}), cur_data.get("k2_metrics", {}), cur_data.get("k4_metrics", {})
            
            with st.form("manual_override_form", border=False):
                st.caption("確認數據無誤後，即可點擊下方按鈕同步上雲端。")
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
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("💾 儲存並同步至雲端", type="primary"):
                    DATA_ENGINE[st.session_state.selected_period]["k1_metrics"]["weekly_push_current"] = new_w_push
                    DATA_ENGINE[st.session_state.selected_period]["k1_metrics"]["total_push_accumulated"] = new_t_push
                    DATA_ENGINE[st.session_state.selected_period]["k1_metrics"]["derived_weekly_new_users"] = new_w_users
                    DATA_ENGINE[st.session_state.selected_period]["k1_metrics"]["actual_total_users"] = new_t_users
                    DATA_ENGINE[st.session_state.selected_period]["k2_metrics"]["new_stores_adjusted"] = new_w_stores
                    DATA_ENGINE[st.session_state.selected_period]["k2_metrics"]["total_stores_accumulated"] = new_t_stores
                    DATA_ENGINE[st.session_state.selected_period]["k4_metrics"]["expire_20260930_coins"] = new_exp26
                    DATA_ENGINE[st.session_state.selected_period]["k4_metrics"]["expire_20270930_coins"] = new_exp27
                    
                    updated_json_str = json.dumps(DATA_ENGINE, ensure_ascii=False, indent=4)
                    
                    with open(JSON_FILE, "w", encoding="utf-8") as f: 
                        f.write(updated_json_str)
                    
                    if "GITHUB_TOKEN" in st.secrets and "GITHUB_REPO" in st.secrets:
                        try:
                            with st.spinner("正在將資料安全同步至雲端 GitHub..."):
                                g = Github(st.secrets["GITHUB_TOKEN"])
                                repo = g.get_repo(st.secrets["GITHUB_REPO"])
                                contents = repo.get_contents("metrics_history.json")
                                repo.update_file(
                                    contents.path,
                                    f"TTPush 自動更新：{st.session_state.selected_period}",
                                    updated_json_str,
                                    contents.sha
                                )
                            st.success("✅ 雲端資料庫同步成功！")
                        except Exception as e:
                            st.error(f"❌ 雲端同步失敗，請檢查權限設定：{e}")
                    else:
                        st.info("ℹ️ 未偵測到 GitHub 金鑰，僅儲存於本地端。")
                        
                    time.sleep(1.5)
                    st.rerun()

        st.markdown("---")
        st.markdown("#### 🚨 Danger Zone")
        with st.expander("🗑️ 刪除當期數據 (無法復原)", expanded=False):
            st.error(f"**警告：** 您即將徹底刪除\n`{st.session_state.selected_period}`\n的所有數據。刪除後將同步覆寫雲端，無法復原！")
            if st.button("🚨 確認徹底刪除", type="primary", use_container_width=True):
                if st.session_state.selected_period in DATA_ENGINE:
                    del DATA_ENGINE[st.session_state.selected_period]
                    
                    updated_json_str = json.dumps(DATA_ENGINE, ensure_ascii=False, indent=4)
                    with open(JSON_FILE, "w", encoding="utf-8") as f:
                        f.write(updated_json_str)
                        
                    if "GITHUB_TOKEN" in st.secrets and "GITHUB_REPO" in st.secrets:
                        try:
                            with st.spinner("正在抹除雲端資料..."):
                                g = Github(st.secrets["GITHUB_TOKEN"])
                                repo = g.get_repo(st.secrets["GITHUB_REPO"])
                                contents = repo.get_contents("metrics_history.json")
                                repo.update_file(
                                    contents.path,
                                    f"TTPush 自動刪除：{st.session_state.selected_period}",
                                    updated_json_str,
                                    contents.sha
                                )
                        except Exception as e:
                            st.error(f"雲端同步刪除失敗: {e}")
                    
                    st.success(f"✅ 數據已徹底抹除，自動恢復上一週狀態！")
                    
                    if DATA_ENGINE:
                        st.session_state.selected_period = sorted(list(DATA_ENGINE.keys()), reverse=True)[0]
                    else:
                        st.session_state.selected_period = "尚無資料"
                        
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error("找不到該週期的資料！")

    elif nav_tab in ["💰 預算管理", "📞 客服紀錄"]:
        st.info("模組擴充準備中...")

    # --- 底部懸浮版本號 (置中極簡) ---
    st.markdown(
        """
        <div class="sidebar-footer-sticky">
            <span style="color: #9ca3af; font-size: 0.9rem; font-weight: 600; letter-spacing: 0.5px;">台東金幣大數據雲端自動化引擎 v11.8</span>
        </div>
        """, 
        unsafe_allow_html=True
    )

# ==========================================
# 4. 📺 主畫面渲染
# ==========================================
if nav_tab in ["👀 戰情首頁", "🔄 週報維護"]:
    
    st.markdown('<div class="fixed-title">TTPush 週營運資料統計分析</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <style>
    section[data-testid="stMain"] div[data-testid="stSelectbox"] {
        margin-top: -60px !important; 
        opacity: 0 !important;        
        z-index: 999 !important;      
        cursor: pointer !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="capsule-visual-container" style="margin-top: 15px; margin-bottom: 5px; position: relative;">
        <div class="morandi-static-capsule">
            {st.session_state.selected_period}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.selectbox(
        "隱形控制核心",
        options=historical_periods_list,
        index=historical_periods_list.index(st.session_state.selected_period) if st.session_state.selected_period in historical_periods_list else 0,
        label_visibility="collapsed",
        key="capsule_hidden_key",
        on_change=on_hidden_capsule_change
    )
    
    current_data = DATA_ENGINE.get(st.session_state.selected_period, {})
    k1_d = current_data.get("k1_metrics", {})
    k2_d = current_data.get("k2_metrics", {})
    k3_d = current_data.get("k3_metrics", {"b110": "176,839,060", "b111": "67,113,280", "b112": "66,302,010", "b113": "104,541,785", "b114": "82,390,693", "b115": "80,681,000"})
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
    b115_val = k3_d.get('b115','80,681,000')

    def parse_budget(val):
        return int(str(val).replace(',', '').strip() or 0)
    
    total_budget_num = parse_budget(b110_val) + parse_budget(b111_val) + parse_budget(b112_val) + parse_budget(b113_val) + parse_budget(b114_val) + parse_budget(b115_val)
    total_budget_str = f"{total_budget_num:,}"

    exp26_str = f"{int(k4_d.get('expire_20260930_coins', 0)):,}"
    exp27_str = f"{int(k4_d.get('expire_20270930_coins', 0)):,}"

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
                    f'<span class="card-label">推播統計</span>'
                    f'<div class="app-list-item">📣 累計：<span class="data-bold">{t_push_str}</span> 則</div>'
                    f'<div class="app-list-item">🚀 本週：<span class="data-bold">{w_push_str}</span> 則</div>'
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
                    f'<span class="card-label">臺東金幣總發放數</span>'
                    f'<div class="hero-val-wrapper">'
                        f'<span class="long-value" style="font-size: 1.8rem; font-weight: 800; line-height: 1.1;">{t_coins_str}</span><span class="unit">枚</span>'
                    f'</div>'
                    f'<div class="section-note-bottom">累積自 110/01/01 起算</div>'
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
                        f'<span class="hero-value">{total_budget_str}</span><span class="unit">枚</span>'
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
