import pandas as pd
import streamlit as st
import json
import os
import io
import datetime
import time
import requests
from github import Github

# ==========================================
# 1. 🌐 全域設定與 CSS 載入
# ==========================================
st.set_page_config(page_title="TTPush 戰情室", layout="wide", initial_sidebar_state="collapsed")

# 移除高風險的 CSS 綁架，回歸原生穩定渲染
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

# 強制將日期由新到舊排序，確保最新一週永遠在最上面
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
# 3. 🎛️ 左側控制台開發 (V11.17 穩定回歸版)
# ==========================================
with st.sidebar:
    st.markdown('<h2 style="margin:0; font-weight: 800; letter-spacing: -0.5px;">🎛️ TTPUSH維運控制台</h2>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    nav_tab = st.radio(
        "請選擇操作情境：",
        options=["👀 戰情首頁", "🔄 週報維護", "💰 預算管理", "📞 客服紀錄"],
        horizontal=False, 
        label_visibility="collapsed"
    )
    st.markdown("<br>", unsafe_allow_html=True)
    
    if nav_tab == "👀 戰情首頁":
        st.info(f"💡 目前戰情室正定錨在：\n\n**{st.session_state.selected_period}**")
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<h4 style="color: #2563eb; font-weight: 800; margin-bottom: 15px;">📥 歷史數據匯出</h4>', unsafe_allow_html=True)
        
        export_records = []
        for period, data in DATA_ENGINE.items():
            if period == "BUDGET_SYSTEM": continue
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
            with col_p3: new_stores_input = st.number_input("📈 本週新增特約店家", min_value=0, step=1, value=0)
            with col_p4: wallet_adj_input = st.number_input("💰 當週會員錢包調整", step=1, value=0)

        st.markdown("##### 📁 報表匯入")
        new_files = st.file_uploader("拖曳本週「綜合報表」與「交易紀錄」：", type=["csv", "xlsx", "xls"], accept_multiple_files=True, label_visibility="collapsed")
        
        if new_files and len(new_files) > 0:
            if st.button("🚀 啟動解析並產生暫存", use_container_width=True, type="primary"):
                report_df, txn_df = None, None
                for f in new_files:
                    is_excel = f.name.endswith(('.xlsx', '.xls'))
                    if "報表" in f.name: report_df = pd.read_excel(f, header=None).fillna("") if is_excel else pd.read_csv(f, header=None).fillna("")
                    elif "交易" in f.name: txn_df = pd.read_excel(f).fillna("") if is_excel else pd.read_csv(f).fillna("")
                
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
                            if any(d in row_str for d in ["2026/09/30", "2026-09-30", "115/09/30"]):
                                for c in row:
                                    val = safe_parse_int(c)
                                    if val is not None and val > 1000 and val != 20260930: exp26_parsed = val
                            if any(d in row_str for d in ["2027/09/30", "2027-09-30", "116/09/30"]):
                                for c in row:
                                    val = safe_parse_int(c)
                                    if val is not None and val > 1000 and val != 20270930: exp27_parsed = val
                        
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
                            "k1_metrics": {"actual_total_users": actual_users, "derived_weekly_new_users": derived_new_users, "total_push_accumulated": actual_total_push, "weekly_push_current": new_push_input},
                            "k2_metrics": {"weekly_coins_issued": adjusted_issued, "weekly_coins_redeemed_audited": redeemed, "active_stores_count": active_stores, "new_stores_adjusted": new_stores_input, "total_accumulated_coins": int(prev_k2.get("total_accumulated_coins", 0)) + adjusted_issued, "total_stores_accumulated": actual_total_stores},
                            "k3_metrics": prev_k3,
                            "k4_metrics": {"expire_20260930_coins": exp26_parsed if exp26_parsed is not None else int(prev_k4.get("expire_20260930_coins", 0)), "expire_20270930_coins": exp27_parsed if exp27_parsed is not None else int(prev_k4.get("expire_20270930_coins", 0))}
                        }
                        
                        with open(BAK_FILE, "w", encoding="utf-8") as bak_f: json.dump(DATA_ENGINE, bak_f, ensure_ascii=False, indent=4)
                        with open(JSON_FILE, "w", encoding="utf-8") as f: json.dump(DATA_ENGINE, f, ensure_ascii=False, indent=4)
                            
                        st.success(f"✅ 解析完成！請展開下方進階面板進行雲端同步。")
                        st.session_state.selected_period = period_key
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 解析失敗: {e}")

        st.markdown("---")
        st.markdown("### 🛠️ 步驟二：審核與同步")
        with st.expander("⚙️ 進階：手動數據微調與雲端同步", expanded=False):
            cur_data = DATA_ENGINE.get(st.session_state.selected_period, {})
            cur_k1, cur_k2, cur_k4 = cur_data.get("k1_metrics", {}), cur_data.get("k2_metrics", {}), cur_data.get("k4_metrics", {})
            with st.form("manual_override_form", border=False):
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
                    with open(JSON_FILE, "w", encoding="utf-8") as f: json.dump(DATA_ENGINE, f, ensure_ascii=False, indent=4)
                    if "GITHUB_TOKEN" in st.secrets and "GITHUB_REPO" in st.secrets:
                        try:
                            g = Github(st.secrets["GITHUB_TOKEN"])
                            repo = g.get_repo(st.secrets["GITHUB_REPO"])
                            contents = repo.get_contents("metrics_history.json")
                            repo.update_file(contents.path, f"TTPush 自動更新：{st.session_state.selected_period}", json.dumps(DATA_ENGINE, ensure_ascii=False, indent=4), contents.sha)
                            st.success("✅ 雲端同步成功！")
                        except: st.error("❌ 雲端同步失敗")
                    time.sleep(1.5)
                    st.rerun()

        st.divider()
        st.markdown("#### 🚨 Danger Zone")
        with st.expander("🗑️ 刪除當期數據 (無法復原)", expanded=False):
            st.error(f"**警告：** 您即將徹底刪除\n`{st.session_state.selected_period}`\n的所有數據。刪除後將同步覆寫雲端，無法復原！")
            if st.button("🚨 確認徹底刪除", type="primary", use_container_width=True):
                if st.session_state.selected_period in DATA_ENGINE:
                    del DATA_ENGINE[st.session_state.selected_period]
                    with open(JSON_FILE, "w", encoding="utf-8") as f: json.dump(DATA_ENGINE, f, ensure_ascii=False, indent=4)
                    st.success(f"✅ 數據已徹底抹除！")
                    st.session_state.selected_period = sorted([k for k in DATA_ENGINE.keys() if k != "BUDGET_SYSTEM"], reverse=True)[0] if len(DATA_ENGINE)>1 else "尚無資料"
                    time.sleep(1)
                    st.rerun()
                    
        st.markdown("---")
        st.markdown("#### ⚙️ 資料庫安全閘門")
        if st.button("💾 手動備份本地資料庫", use_container_width=True):
            with open(BAK_FILE, "w", encoding="utf-8") as bak_f: json.dump(DATA_ENGINE, bak_f, ensure_ascii=False, indent=4)
            st.success("備份完畢")

    elif nav_tab == "📞 客服紀錄":
        st.info("模組擴充準備中...")

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""<div style="text-align: center; color: #9ca3af; font-size: 0.9rem; font-weight: 600; letter-spacing: 0.5px;">台東金幣大數據雲端自動化引擎 v11.21</div>""", unsafe_allow_html=True)


# ==========================================
# 4. 📺 主畫面渲染 - 戰情首頁
# ==========================================
if nav_tab == "👀 戰情首頁" or nav_tab == "🔄 週報維護":
    st.markdown('<div class="fixed-title">TTPush 週營運資料統計分析</div>', unsafe_allow_html=True)
    st.markdown("""<style>section[data-testid="stMain"] div[data-testid="stSelectbox"] { margin-top: -60px !important; opacity: 0 !important; z-index: 999 !important; cursor: pointer !important; }</style>""", unsafe_allow_html=True)
    st.markdown(f"""<div class="capsule-visual-container" style="margin-top: 15px; margin-bottom: 5px; position: relative;"><div class="morandi-static-capsule">{st.session_state.selected_period}</div></div>""", unsafe_allow_html=True)
    st.selectbox("隱形控制核心", options=historical_periods_list, index=historical_periods_list.index(st.session_state.selected_period) if st.session_state.selected_period in historical_periods_list else 0, label_visibility="collapsed", key="capsule_hidden_key", on_change=on_hidden_capsule_change)
    
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

    def parse_budget(val): return int(str(val).replace(',', '').strip() or 0)
    total_budget_str = f"{parse_budget(b110_val)+parse_budget(b111_val)+parse_budget(b112_val)+parse_budget(b113_val)+parse_budget(b114_val)+parse_budget(b115_val):,}"

    exp26_str = f"{int(k4_d.get('expire_20260930_coins', 0)):,}"
    exp27_str = f"{int(k4_d.get('expire_20270930_coins', 0)):,}"

    k1, k2, k3, k4 = st.columns([0.9, 1, 1.2, 1.2])
    with k1: st.markdown(f'<div class="unified-card k1-card"><div class="card-section-top"><span class="card-label">累積會員總數</span><div class="hero-val-wrapper"><span class="hero-value">{t_users_str}</span><span class="unit">人</span></div><div class="growth-tag">▲ 本週新增 +{w_users_str} 人</div></div><div class="divider-line-center"></div><div class="card-section-bottom"><span class="card-label">推播統計</span><div class="app-list-item">📣 累計：<span class="data-bold">{t_push_str}</span> 則</div><div class="app-list-item">🚀 本週：<span class="data-bold">{w_push_str}</span> 則</div></div></div>', unsafe_allow_html=True)
    with k2: st.markdown(f'<div class="unified-card k2-card"><div class="card-section-top"><span class="card-label">當週指標</span><div class="app-list-item" style="margin-top: 8px;">✨ 當週發放：<span class="data-bold">{w_issued_str}</span> 枚</div><div class="app-list-item">🎁 當週兌換：<span class="data-bold">{w_redeemed_str}</span> 枚</div><div class="app-list-item">💲 消費店家：<span class="data-bold">{active_stores_str}</span> 家</div><div class="app-list-item">🏪 總特約店：<span class="data-bold">{total_stores_str}</span> 家</div><div class="app-list-item">📈 新增店家：<span class="data-bold">+{new_stores_str}</span> 家</div></div><div class="divider-line-center"></div><div class="card-section-bottom"><span class="card-label">臺東金幣總發放數</span><div class="hero-val-wrapper"><span class="long-value" style="font-size: 1.8rem; font-weight: 800; line-height: 1.1;">{t_coins_str}</span><span class="unit">枚</span></div><div class="section-note-bottom">累積自 110/01/01 起算</div></div></div>', unsafe_allow_html=True)
    with k3: st.markdown(f'<div class="unified-card k3-card"><div class="card-section-top"><span class="card-label">臺東金幣總預算數</span><div class="hero-val-wrapper"><span class="hero-value">{total_budget_str}</span><span class="unit">枚</span></div><div class="section-note-top-k3">累計 110至115年度預算(11-17期)</div></div><div class="divider-line-center"></div><div class="card-section-bottom"><span class="card-label">📅 歷年預算明細</span><div class="budget-grid"><div class="budget-item"><span class="b-year">110年/11+12期</span><span class="val">{b110_val}</span><span class="b-unit">枚</span></div><div class="budget-item"><span class="b-year">111年/13期</span><span class="val">{b111_val}</span><span class="b-unit">枚</span></div><div class="budget-item"><span class="b-year">112年/14期</span><span class="val">{b112_val}</span><span class="b-unit">枚</span></div><div class="budget-item"><span class="b-year">113年/15期</span><span class="val">{b113_val}</span><span class="b-unit">枚</span></div><div class="budget-item"><span class="b-year">114年/16期</span><span class="val">{b114_val}</span><span class="b-unit">枚</span></div><div class="budget-item"><span class="b-year">115年/17期</span><span class="val">{b115_val}</span><span class="b-unit">枚</span></div></div></div></div>', unsafe_allow_html=True)
    with k4: st.markdown(f'<div class="unified-card k4-card"><div class="card-section-top"><span class="card-label">⚠️ 金幣到期預警</span><div class="expire-list-container"><div class="expire-row"><span class="expire-date">2026/09/30 到期</span><div class="expire-val-wrapper"><span class="expire-number">{exp26_str}</span><span class="expire-unit">枚</span></div></div><div class="expire-row"><span class="expire-date">2027/09/30 到期</span><div class="expire-val-wrapper"><span class="expire-number">{exp27_str}</span><span class="expire-unit">枚</span></div></div></div></div><div class="divider-line-center"></div><div class="card-section-bottom"><span class="card-label">📢 營運備註整理</span><ul class="ops-notes"><li><span class="note-tag">維護</span>114/06/04 因 4.0 上線系統關閉維護</li><li><span class="note-tag">封測</span>114/06/23-27 進行 4.0 核心封測</li><li><span class="note-tag">推播</span>113/09/25-11/06 暫停金幣推播</li><li><span class="note-tag">對象</span>推播含所有用戶及縣民群組</li><li><span class="note-tag">基準</span>金幣統計自 110/01/01 起算</li></ul></div></div>', unsafe_allow_html=True)

# ==========================================
# 5. 💰 預算管理模組 (V11.21 Apps Script 微型伺服器版)
# ==========================================
elif nav_tab == "💰 預算管理":
    st.markdown('<h2 style="color: #1e3a8a; font-weight: 800; margin-bottom: 5px;">💰 預算管理與局處動支分配表</h2>', unsafe_allow_html=True)
    
    # 🌟 已經修復網址重疊的錯誤！這是您的專屬正確網址
    API_URL = "https://script.google.com/a/macros/dotdot.cc/s/AKfycbwpVyokJqFK8tB6U6RS0fX70voQ_ro1RMtF4PRVtq5hRVwziqkY9VeUOYwrXHPnWrM0dg/exec"
    
    # --- 定義雙向拋接的大腦 ---
    def fetch_sheet(sheet_name):
        try:
            res = requests.post(API_URL, json={"action": "read", "sheet_name": sheet_name})
            data = res.json().get("data", [])
            if data and len(data) > 1:
                return pd.DataFrame(data[1:], columns=data[0])
            elif data and len(data) == 1:
                return pd.DataFrame(columns=data[0])
            return pd.DataFrame()
        except:
            return pd.DataFrame()

    def update_sheet(sheet_name, df):
        # 將 DataFrame 轉回 2D 陣列格式傳給 Google Sheet
        data_to_send = [df.columns.tolist()] + df.values.tolist()
        requests.post(API_URL, json={"action": "update", "sheet_name": sheet_name, "data": data_to_send})

    # --- 執行讀取 ---
    with st.spinner("🔄 正在從 Google Sheets 雲端拋接最新數據..."):
        df_master = fetch_sheet("Master")
        df_log = fetch_sheet("Log")
        
        # 確保資料格式正確，避免空表引發錯誤
        if not df_master.empty:
            df_master["年度"] = df_master["年度"].astype(int)
            df_master["分配額度"] = df_master["分配額度"].astype(int)
        else:
            df_master = pd.DataFrame(columns=["年度", "局處名稱", "預算類別", "分配額度"])

        if not df_log.empty:
            df_log["動支金額"] = df_log["動支金額"].astype(int)
        else:
            df_log = pd.DataFrame(columns=["日期", "局處名稱", "預算類別", "用途說明", "動支金額"])

    # 🌟 補回剛剛消失的 UI 介面代碼
    all_depts = sorted(list(set(df_master["局處名稱"].tolist() + df_log["局處名稱"].tolist()))) if not df_master.empty or not df_log.empty else []
    
    report_rows = []
    for dept in all_depts:
        m_orig = df_master[(df_master["局處名稱"] == dept) & (df_master["預算類別"] == "原始分配")]["分配額度"].sum() if not df_master.empty else 0
        l_orig = df_log[(df_log["局處名稱"] == dept) & (df_log["預算類別"] == "原始分配")]["動支金額"].sum() if not df_log.empty else 0
        r_orig = m_orig - l_orig
        
        m_proj = df_master[(df_master["局處名稱"] == dept) & (df_master["預算類別"] == "計畫型預算")]["分配額度"].sum() if not df_master.empty else 0
        l_proj = df_log[(df_log["局處名稱"] == dept) & (df_log["預算類別"] == "計畫型預算")]["動支金額"].sum() if not df_log.empty else 0
        r_proj = m_proj - l_proj
        
        report_rows.append({
            "局處名稱": dept,
            "原始分配-核定額度": int(m_orig),
            "原始分配-已動支": int(l_orig),
            "原始分配-可用餘額": int(r_orig),
            "計畫型預算-核定額度": int(m_proj),
            "計畫型預算-已動支": int(l_proj),
            "計畫型預算-可用餘額": int(r_proj),
            "總可用餘額(合計)": int(r_orig + r_proj)
        })
        
    df_weekly_report = pd.DataFrame(report_rows) if report_rows else pd.DataFrame(
        columns=["局處名稱", "原始分配-核定額度", "原始分配-已動支", "原始分配-可用餘額", "計畫型預算-核定額度", "計畫型預算-已動支", "計畫型預算-可用餘額", "總可用餘額(合計)"]
    )

    tab1, tab2, tab3 = st.tabs(["📊 局處額度總表 (每週報表匯出)", "⚙️ 總分配設定 (Master)", "✍️ 動支流水帳 (Log)"])
    
    with tab1:
        st.markdown("#### 🏢 復刻版週報：各局處雙水庫額度動支對照表")
        st.caption("即時連動 Google Sheets 最新帳目。左半邊計算原始預算，右半邊計算計畫型預算，相互獨立不混淆。")
        
        if not df_weekly_report.empty:
            df_display = df_weekly_report.copy()
            for col in df_display.columns:
                if col != "局處名稱":
                    df_display[col] = df_display[col].apply(lambda x: f"{x:,}")
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_weekly_report.to_excel(writer, index=False, sheet_name='局處可用餘額週報')
            output.seek(0)
            
            st.download_button(
                label="📥 一鍵下載本週局處報表 (Excel)", data=output,
                file_name=f"TTPush_局處可用餘額週報_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )
            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.warning("目前雲端試算表尚無任何預算設定資料，請至「總分配設定」分頁建立。")

    with tab2:
        st.markdown("#### ⚙️ 編輯：年度總預算與局處核定分配池")
        st.caption("雙擊欄位可修改數值，可在最下方表格空白列直接打字新增局處。")
        edited_master = st.data_editor(
            df_master, 
            num_rows="dynamic", 
            use_container_width=True,
            column_config={
                "年度": st.column_config.NumberColumn("年度", required=True, format="%d"),
                "局處名稱": st.column_config.TextColumn("局處名稱", required=True),
                "預算類別": st.column_config.SelectboxColumn("預算類別", options=["原始分配", "計畫型預算"], required=True),
                "分配額度": st.column_config.NumberColumn("分配額度 (金幣數)", required=True, min_value=0)
            },
            key="editor_master"
        )

    with tab3:
        st.markdown("#### ✍️ 編輯：日常發放動支流水帳")
        st.caption("請確實選擇正確的動支水庫（原始分配/計畫型預算），系統將自動為該局處獨立扣除額度。")
        edited_log = st.data_editor(
            df_log, 
            num_rows="dynamic", 
            use_container_width=True,
            column_config={
                "日期": st.column_config.TextColumn("日期 (例如: 115/06/26)", required=True),
                "局處名稱": st.column_config.TextColumn("局處名稱", required=True),
                "預算類別": st.column_config.SelectboxColumn("預算類別", options=["原始分配", "計畫型預算"], required=True),
                "用途說明": st.column_config.TextColumn("用途說明", required=True),
                "動支金額": st.column_config.NumberColumn("動支金額 (金幣數)", required=True, min_value=0)
            },
            key="editor_log"
        )
        
    st.markdown("---")
    # --- 儲存並透過 API 寫入 Google 表單 ---
    if st.button("💾 儲存預算變更並即時同步至 Google Sheets", type="primary", use_container_width=True):
        with st.spinner("🚀 正在將最新數據原子級寫入 Google Sheets..."):
            final_master = edited_master.dropna(subset=["局處名稱", "分配額度"])
            final_log = edited_log.dropna(subset=["局處名稱", "動支金額"])
            
            # 呼叫我們自己寫的 API 寫回 Google 表單
            update_sheet("Master", final_master)
            update_sheet("Log", final_log)
            
            # 連動 K3 總額的邏輯維持不變
            total_115_pool = final_master[final_master["年度"].astype(str) == "115"]["分配額度"].sum() if not final_master.empty else 0
            if st.session_state.selected_period in DATA_ENGINE and st.session_state.selected_period != "尚無資料":
                DATA_ENGINE[st.session_state.selected_period]["k3_metrics"]["b115"] = f"{int(total_115_pool):,}"
            
            with open(JSON_FILE, "w", encoding="utf-8") as f:
                json.dump(DATA_ENGINE, f, ensure_ascii=False, indent=4)
                
            st.success("🎉 完美落地！資料已成功寫入 Google 試算表，首頁 K3 也已連動！")
            time.sleep(1.5)
            st.rerun()
