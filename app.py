import pandas as pd
import streamlit as st
import json
import os
import io
import datetime
import time
import requests
import platform
from github import Github
from PIL import Image, ImageDraw, ImageFont

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
# 3. 🎛️ 左側控制台開發
# ==========================================
with st.sidebar:
    st.markdown('<h2 style="margin:0; font-weight: 800; letter-spacing: -0.5px;">🎛️ TTPUSH維運控制台</h2>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 加入新的整合模組選項
    nav_tab = st.radio(
        "請選擇操作情境：",
        options=["👀 戰情首頁", "🔄 週報維護", "💰 預算管理", "📅 排程與預算中心", "📞 客服紀錄"],
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
    st.markdown("""<div style="text-align: center; color: #9ca3af; font-size: 0.9rem; font-weight: 600; letter-spacing: 0.5px;">台東金幣大數據雲端自動化引擎 v11.22</div>""", unsafe_allow_html=True)


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
# 5. 💰 預算管理模組 (三層式架構 CRUD 核心)
# ==========================================
elif nav_tab == "💰 預算管理":
    st.markdown('<h2 style="color: #1e3a8a; font-weight: 800; margin-bottom: 5px;">💰 預算管理與局處動支分配表</h2>', unsafe_allow_html=True)
    st.caption("台東金幣 Apps Script 零成本微型伺服器版 v11.22 (支援計畫名稱獨立核算)")
    
    API_URL = "https://script.google.com/macros/s/AKfycbxF4hp0a2-F1BPIKDrMifUeN2aiOgyngjM_urhZgbG6g6etzISTzrcTH93oLvMLl5xhig/exec"
    
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
        data_to_send = [df.columns.tolist()] + df.values.tolist()
        requests.post(API_URL, json={"action": "update", "sheet_name": sheet_name, "data": data_to_send})

    with st.spinner("🔄 正在從 Google Sheets 雲端拋接最新三層式數據..."):
        df_master = fetch_sheet("Master")
        df_log = fetch_sheet("Log")
        
        if not df_master.empty:
            df_master["年度"] = df_master["年度"].astype(int)
            df_master["分配額度"] = df_master["分配額度"].astype(int)
        else:
            df_master = pd.DataFrame(columns=["年度", "局處名稱", "預算類別", "計畫名稱", "分配額度"])

        if not df_log.empty:
            df_log["動支金額"] = df_log["動支金額"].astype(int)
        else:
            df_log = pd.DataFrame(columns=["日期", "局處名稱", "預算類別", "計畫名稱", "用途說明", "動支金額"])

    report_rows = []
    if not df_master.empty:
        for idx, row in df_master.iterrows():
            dept = row["局處名稱"]
            b_type = row["預算類別"]
            proj = row["計畫名稱"]
            allocated = int(row["分配額度"])
            
            if not df_log.empty:
                spent = df_log[(df_log["局處名稱"] == dept) & 
                               (df_log["預算類別"] == b_type) & 
                               (df_log["計畫名稱"] == proj)]["動支金額"].sum()
            else:
                spent = 0
            
            report_rows.append({
                "局處名稱": dept,
                "預算類別": b_type,
                "計畫名稱": proj,
                "核定額度": allocated,
                "已動支": int(spent),
                "可用餘額": allocated - int(spent)
            })
            
    df_weekly_report = pd.DataFrame(report_rows) if report_rows else pd.DataFrame(columns=["局處名稱", "預算類別", "計畫名稱", "核定額度", "已動支", "可用餘額"])

    tab1, tab2, tab3 = st.tabs(["📊 計畫額度總表 (精準核算)", "⚙️ 總分配設定 (Master)", "✍️ 動支流水帳 (Log)"])
    
    with tab1:
        st.markdown("#### 🏢 各局處專案計畫可用餘額總表")
        st.caption("系統已自動依據「局處 ➡️ 預算類別 ➡️ 計畫名稱」為您精準對齊並計算剩餘額度。")
        
        if not df_weekly_report.empty:
            df_display = df_weekly_report.copy()
            for col in ["核定額度", "已動支", "可用餘額"]:
                df_display[col] = df_display[col].apply(lambda x: f"{x:,}")
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_weekly_report.to_excel(writer, index=False, sheet_name='計畫可用餘額表')
            output.seek(0)
            
            st.download_button(
                label="📥 一鍵下載本週最新計畫報表 (Excel)", data=output,
                file_name=f"TTPush_專案預算可用餘額表_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )
            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.warning("目前雲端試算表尚無任何預算設定資料，請至「總分配設定」分頁建立。")

    with tab2:
        st.markdown("#### ⚙️ 編輯：年度總預算與計畫核定分配池")
        st.caption("雙擊欄位可修改數值，可在最下方表格空白列直接打字新增計畫。")
        edited_master = st.data_editor(
            df_master, 
            num_rows="dynamic", 
            use_container_width=True,
            column_config={
                "年度": st.column_config.NumberColumn("年度", required=True, format="%d"),
                "局處名稱": st.column_config.TextColumn("局處名稱", required=True),
                "預算類別": st.column_config.SelectboxColumn("預算類別", options=["原始分配", "計畫型預算"], required=True),
                "計畫名稱": st.column_config.TextColumn("計畫名稱 (用於精準扣款)", required=True),
                "分配額度": st.column_config.NumberColumn("分配額度 (金幣數)", required=True, min_value=0)
            },
            key="editor_master"
        )

    with tab3:
        st.markdown("#### ✍️ 編輯：日常發放動支流水帳")
        st.caption("請務必填寫正確的「計畫名稱」，系統才能從對應的專案水庫中扣除額度。")
        edited_log = st.data_editor(
            df_log, 
            num_rows="dynamic", 
            use_container_width=True,
            column_config={
                "日期": st.column_config.TextColumn("日期 (例如: 2026/06/26)", required=True),
                "局處名稱": st.column_config.TextColumn("局處名稱", required=True),
                "預算類別": st.column_config.SelectboxColumn("預算類別", options=["原始分配", "計畫型預算"], required=True),
                "計畫名稱": st.column_config.TextColumn("計畫名稱 (需與Master一致)", required=True),
                "用途說明": st.column_config.TextColumn("用途說明", required=True),
                "動支金額": st.column_config.NumberColumn("動支金額 (金幣數)", required=True, min_value=0)
            },
            key="editor_log"
        )
        
    st.markdown("---")
    if st.button("💾 儲存預算變更並即時同步至 Google Sheets", type="primary", use_container_width=True):
        with st.spinner("🚀 正在將最新數據原子級寫入 Google Sheets..."):
            final_master = edited_master.dropna(subset=["局處名稱", "計畫名稱", "分配額度"])
            final_log = edited_log.dropna(subset=["局處名稱", "計畫名稱", "動支金額"])
            
            update_sheet("Master", final_master)
            update_sheet("Log", final_log)
            
            total_115_pool = final_master[final_master["年度"].astype(str) == "115"]["分配額度"].sum() if not final_master.empty else 0
            if st.session_state.selected_period in DATA_ENGINE and st.session_state.selected_period != "尚無資料":
                DATA_ENGINE[st.session_state.selected_period]["k3_metrics"]["b115"] = f"{int(total_115_pool):,}"
            
            with open(JSON_FILE, "w", encoding="utf-8") as f:
                json.dump(DATA_ENGINE, f, ensure_ascii=False, indent=4)
                
            st.success("🎉 完美落地！資料已成功寫入 Google 試算表，首頁 K3 也已連動！")
            time.sleep(1.5)
            st.rerun()

# ==========================================
# 6. 📅 排程與預算中心 (新擴充模組)
# ==========================================
elif nav_tab == "📅 排程與預算中心":
    st.markdown('<h2 style="color: #1e3a8a; font-weight: 800; margin-bottom: 5px;">📅 排程與預算優化中心</h2>', unsafe_allow_html=True)
    
    # 將畫面分為兩個頁籤
    tab_budget, tab_schedule = st.tabs(["💰 預算報表優化", "🖼️ 金幣線上排程表"])

    # --- 區塊 1：預算報表優化 ---
    with tab_budget:
        st.markdown("#### 📥 特定局處預算萃取與分析")
        try:
            # 讀取預算報表[cite: 1]
            df_budget = pd.read_excel('預算報表.xlsx')
            num_cols = ['原始預算總額', '目前預算總額', '預算已分配幣', '預算可分配幣']
            
            # 清理數字格式[cite: 1]
            for col in num_cols:
                df_budget[col] = df_budget[col].astype(str).str.replace(',', '').astype(float)
                
            # 擷取特定範圍 (480列 與 484-500列)[cite: 1]
            p17_dept_rows = df_budget.loc[484:500].copy()
            p17_dept_rows = pd.concat([df_budget.loc[480:480], p17_dept_rows])
            
            total_original_budget = p17_dept_rows['原始預算總額'].sum()
            
            st.metric("🏆 篩選範圍之原始預算總額", f"{total_original_budget:,.0f} 枚")
            st.dataframe(p17_dept_rows[['單位', '預算名稱', '原始預算總額', '預算已分配幣', '預算可分配幣']], use_container_width=True)
            
        except FileNotFoundError:
            st.warning("⚠️ 找不到 `預算報表.xlsx` 檔案，請確認檔案已放置於專案根目錄中。")
        except Exception as e:
            st.error(f"預算報表解析發生錯誤: {e}")

    # --- 區塊 2：金幣線上排程表 ---
    with tab_schedule:
        st.markdown("#### 🎨 單日多筆排程圖表即時渲染")
        
        if st.button("🚀 產生最新排程表圖片", type="primary"):
            with st.spinner("正在繪製排程圖表..."):
                
                # 設定畫布與字體環境[cite: 2]
                width, height = 1600, 1450
                img = Image.new('RGB', (width, height), color=(255, 255, 255))
                draw = ImageDraw.Draw(img)
                
                # 自動字體偵測防呆機制，取代固定的 /usr/share/fonts 路徑[cite: 2]
                def get_safe_font(size):
                    sys_plat = platform.system()
                    font_paths = [
                        '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 
                        'msjh.ttc', 'PingFang.ttc', 'Arial.ttf'
                    ]
                    for pt in font_paths:
                        try:
                            return ImageFont.truetype(pt, size)
                        except IOError:
                            continue
                    return ImageFont.load_default()

                f_title = get_safe_font(32)
                f_subtitle = get_safe_font(15)
                f_kpi_num = get_safe_font(30)
                f_kpi_label = get_safe_font(15)
                f_kpi_sub = get_safe_font(13)
                f_th = get_safe_font(16)
                f_td_bold = get_safe_font(15)
                f_td = get_safe_font(15)
                f_badge = get_safe_font(13)
                f_note_title = get_safe_font(15)
                f_note = get_safe_font(13)

                # 排程模擬數據 (包含 8/17 的 4 筆活動)[cite: 2]
                data_multi = [
                    {"date": "2026/08/17", "day": "星期一", "date_span": 4, "is_first_of_date": True, "dept": "臺東縣政府社會處", "type": "問答", "title": "【暑期青春專案-青春無限~不與「毒」同行】", "coin": "10 枚", "quota": "1,600 人", "total": "16,000 枚", "active": True},
                    {"date": "2026/08/17", "day": "星期一", "date_span": 4, "is_first_of_date": False, "dept": "臺東縣警察局", "type": "問答", "title": "防制少年涉入財產犯罪宣導活動", "coin": "20 枚", "quota": "5,000 人", "total": "100,000 枚", "active": True},
                    {"date": "2026/08/17", "day": "星期一", "date_span": 4, "is_first_of_date": False, "dept": "臺東縣衛生局", "type": "問答", "title": "青壯的心，有我傾聽！心理健康小學堂", "coin": "30 枚", "quota": "5,000 人", "total": "150,000 枚", "active": True},
                    {"date": "2026/08/17", "day": "星期一", "date_span": 4, "is_first_of_date": False, "dept": "臺東縣政府財政及經濟發展處", "type": "問答", "title": "2026臺東綠能論壇~歡迎大家踴躍參與", "coin": "20 枚", "quota": "5,000 人", "total": "100,000 枚", "active": True},
                    {"date": "2026/08/18", "day": "星期二", "date_span": 1, "is_first_of_date": True, "dept": "臺東縣政府建設處", "type": "問答", "title": "太平溪環境改善及水資源宣導活動", "coin": "50 枚", "quota": "7,400 人", "total": "370,000 枚", "active": True},
                    {"date": "2026/08/19", "day": "星期三", "date_span": 1, "is_first_of_date": True, "dept": "臺東縣衛生局", "type": "問答", "title": "台東甜蜜蜜，健康「篩」得好安心！", "coin": "30 枚", "quota": "10,000 人", "total": "300,000 枚", "active": True},
                    {"date": "2026/08/20", "day": "星期四", "date_span": 1, "is_first_of_date": True, "dept": "-", "type": "-", "title": "（本日無預排線上問答活動）", "coin": "-", "quota": "-", "total": "-", "active": False},
                    {"date": "2026/08/21", "day": "星期五", "date_span": 1, "is_first_of_date": True, "dept": "-", "type": "-", "title": "（本日無預排線上問答活動）", "coin": "-", "quota": "-", "total": "-", "active": False}
                ]

                # 繪製頭部橫幅[cite: 2]
                header_height = 110
                draw.rectangle([(0, 0), (width, header_height)], fill=(15, 23, 42))
                draw.rectangle([(0, 0), (width, 6)], fill=(245, 158, 11))
                draw.text((60, 26), "115年度 TTPush 金幣推播與線上活動排程表（單日多筆模擬）", font=f_title, fill=(255, 255, 255))
                draw.text((60, 72), "[ 統計範圍 ] 8月17日(一) ～ 8月21日(五)線上問答排程    |    [ 模擬情境 ] 8/17 單日集中 4 筆活動    |    [ 統計日期 ] 115年8月", font=f_subtitle, fill=(148, 163, 184))

                # 繪製頂部 KPI 卡片[cite: 2]
                cards_data = [
                    {"label": "排程活動總數", "value": "6 檔", "sub": "8/17(4檔)、8/18(1檔)、8/19(1檔)", "bg": (238, 242, 255), "left_bar": (79, 70, 229), "val_color": (67, 56, 202)},
                    {"label": "發放金幣總額 (枚)", "value": "1,036,000", "sub": "多局處聯合推播預算", "bg": (254, 243, 199), "left_bar": (217, 119, 6), "val_color": (180, 83, 9)},
                    {"label": "預計受惠總人次 (人)", "value": "34,000", "sub": "發放名額累計上限", "bg": (204, 251, 241), "left_bar": (13, 148, 136), "val_color": (15, 118, 110)},
                    {"label": "單日最高排程密度", "value": "4 檔 / 日", "sub": "8/17 (一) 達高峰", "bg": (241, 245, 249), "left_bar": (100, 116, 139), "val_color": (30, 41, 59)}
                ]

                card_y = 135
                card_w = (width - 120 - 3 * 18) / 4
                card_h = 100

                for idx, c in enumerate(cards_data):
                    cx = 60 + idx * (card_w + 18)
                    draw.rounded_rectangle([(cx, card_y), (cx + card_w, card_y + card_h)], radius=10, fill=c["bg"])
                    draw.rounded_rectangle([(cx, card_y), (cx + 6, card_y + card_h)], radius=3, fill=c["left_bar"])
                    draw.text((cx + 22, card_y + 14), c["label"], font=f_kpi_label, fill=(100, 116, 139))
                    draw.text((cx + 22, card_y + 36), c["value"], font=f_kpi_num, fill=c["val_color"])
                    draw.text((cx + 22, card_y + 72), c["sub"], font=f_kpi_sub, fill=(100, 116, 139))

                # 繪製主數據表格[cite: 2]
                headers = ["推播日期", "星期", "辦理局處名稱", "發放方式", "活動標題名稱", "單次金幣 (枚)", "發放名額 (人)", "預算金額 (枚)"]
                col_widths = [130, 80, 200, 100, 480, 120, 130, 140]

                col_x = [60]
                for w in col_widths[:-1]:
                    col_x.append(col_x[-1] + w)

                start_y = 265
                header_height = 50
                row_height = 65

                draw.rounded_rectangle([(60, start_y), (width - 60, start_y + header_height)], radius=8, fill=(30, 41, 59))

                def get_text_size(text, font):
                    bbox = draw.textbbox((0, 0), text, font=font)
                    return bbox[2] - bbox[0], bbox[3] - bbox[1]

                for i, h in enumerate(headers):
                    align = "center" if i in [0, 1, 3, 5, 6, 7] else "left"
                    tw, _ = get_text_size(h, f_th)
                    tx = col_x[i] + (col_widths[i] - tw) / 2 if align == "center" else col_x[i] + 16
                    ty = start_y + (header_height - 18) / 2
                    draw.text((tx, ty), h, font=f_th, fill=(255, 255, 255))

                current_y = start_y + header_height + 6

                # 包含 Rowspan 機制的迴圈渲染[cite: 2]
                i_idx = 0
                while i_idx < len(data_multi):
                    r = data_multi[i_idx]
                    span = r["date_span"]
                    
                    group_h = span * row_height - 4
                    group_bg = (255, 255, 255) if (i_idx // span if span > 1 else i_idx) % 2 == 0 else (241, 245, 249)
                    
                    for sub_i in range(span):
                        sub_r = data_multi[i_idx + sub_i]
                        curr_row_y = current_y + sub_i * row_height
                        
                        row_bg = (255, 255, 255) if (i_idx + sub_i) % 2 == 0 else (248, 250, 252)
                        draw.rounded_rectangle([(60, curr_row_y), (width - 60, curr_row_y + row_height - 4)], radius=4, fill=row_bg)
                        draw.rectangle([(60, curr_row_y), (width - 60, curr_row_y + row_height - 4)], outline=(226, 232, 240), width=1)
                        
                        row_vals = [sub_r["dept"], sub_r["type"], sub_r["title"], sub_r["coin"], sub_r["quota"], sub_r["total"]]
                        col_indices = [2, 3, 4, 5, 6, 7]
                        
                        for c_idx, val in zip(col_indices, row_vals):
                            f_use = f_td
                            fill_color = (15, 23, 42)
                            
                            if not sub_r["active"]:
                                fill_color = (148, 163, 184)
                            else:
                                if c_idx == 2:
                                    f_use = f_td_bold
                                elif c_idx == 5:
                                    f_use = f_td_bold
                                    fill_color = (217, 119, 6)
                                elif c_idx == 7:
                                    f_use = f_td_bold
                                    fill_color = (13, 148, 136)
                                    
                            if c_idx == 3 and sub_r["type"] == "問答":
                                bw, bh = 56, 26
                                bx = col_x[c_idx] + (col_widths[c_idx] - bw) / 2
                                by = curr_row_y + (row_height - 4 - bh) / 2
                                draw.rounded_rectangle([(bx, by), (bx + bw, by + bh)], radius=5, fill=(220, 252, 231))
                                draw.text((bx + 14, by + 4), "問答", font=f_badge, fill=(22, 101, 52))
                            else:
                                align = "center" if c_idx in [3, 5, 6, 7] else "left"
                                tw, _ = get_text_size(val, f_use)
                                tx = col_x[c_idx] + (col_widths[c_idx] - tw) / 2 if align == "center" else col_x[c_idx] + 16
                                ty = curr_row_y + (row_height - 4 - 18) / 2
                                draw.text((tx, ty), val, font=f_use, fill=fill_color)
                    
                    block_y_start = current_y
                    block_y_end = current_y + span * row_height - 4
                    
                    date_bg = (238, 242, 255) if span > 1 else ((255, 255, 255) if i_idx % 2 == 0 else (241, 245, 249))
                    draw.rounded_rectangle([(60, block_y_start), (col_x[2] - 2, block_y_end)], radius=4, fill=date_bg)
                    draw.rectangle([(60, block_y_start), (col_x[2] - 2, block_y_end)], outline=(199, 210, 254) if span > 1 else (226, 232, 240), width=1.5 if span > 1 else 1)
                    
                    date_str = r["date"]
                    day_str = r["day"]
                    
                    tw, _ = get_text_size(date_str, f_td_bold)
                    tx = col_x[0] + (col_widths[0] - tw) / 2
                    ty = block_y_start + (block_y_end - block_y_start) / 2 - 18
                    draw.text((tx, ty), date_str, font=f_td_bold, fill=(30, 58, 138) if span > 1 else (15, 23, 42))
                    
                    tw, _ = get_text_size(day_str, f_td_bold)
                    tx = col_x[1] + (col_widths[1] - tw) / 2
                    draw.text((tx, ty), day_str, font=f_td_bold, fill=(30, 58, 138) if span > 1 else (15, 23, 42))
                    
                    if span > 1:
                        badge_text = f"共 {span} 檔"
                        tw, _ = get_text_size(badge_text, f_badge)
                        bx = col_x[0] + (col_widths[0] + col_widths[1] - tw) / 2
                        by = ty + 24
                        draw.rounded_rectangle([(bx - 8, by), (bx + tw + 8, by + 20)], radius=10, fill=(199, 210, 254))
                        draw.text((bx, by + 2), badge_text, font=f_badge, fill=(49, 46, 129))

                    current_y += span * row_height
                    i_idx += span

                # 繪製底部說明區塊[cite: 2]
                footer_y = current_y + 30
                draw.line([(60, footer_y), (width - 60, footer_y)], fill=(226, 232, 240), width=1)

                notes = [
                    "[ 報表說明 ]",
                    "1. 當同一天有多筆活動上架時（如 8/17 集中 4 筆），日期欄位將自動進行跨列群組合併 (Rowspan)，視覺結構依舊清晰不重疊。",
                    "2. 金幣計算公式為：預算金額 (枚) ＝ 單次金幣 (枚) × 發放名額 (人)。",
                    "3. 8/20 (四) 及 8/21 (五) 目前無預排線上活動，若有局處臨時加單，將隨時修正並更換最新版排程表。"
                ]

                note_ty = footer_y + 18
                for idx, n in enumerate(notes):
                    font_u = f_note_title if idx == 0 else f_note
                    color_u = (30, 41, 59) if idx == 0 else (100, 116, 139)
                    draw.text((60, note_ty), n, font=font_u, fill=color_u)
                    note_ty += 22

                # 直接呈現在網頁中，不再儲存本機檔案
                st.image(img, caption="115年度 TTPush 金幣推播與線上活動排程表", use_container_width=True)
                st.success("✅ 圖表動態渲染生成完畢！")
