import datetime
import io
import json
import os
import time
import pandas as pd
import streamlit as st

# ==========================================
# 1. 架構：頁面配置與樣式表讀取
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
# 2. 邏輯：持久化 JSON 日誌庫自動載入管線
# ==========================================
JSON_FILE = "metrics_history.json"
BAK_FILE = "metrics_history.json.bak"

def load_historical_data():
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

DATA_ENGINE = load_historical_data()

historical_periods_list = sorted(
    list(DATA_ENGINE.keys()), 
    key=lambda x: x.split("：")[-1].split(" — ")[0] if " — " in x else x, 
    reverse=True
)

if not historical_periods_list:
    historical_periods_list = ["統計區間：115/05/22 — 115/05/28"]

if "selected_period" not in st.session_state:
    st.session_state.selected_period = historical_periods_list[0]

if st.session_state.selected_period not in historical_periods_list:
    st.session_state.selected_period = historical_periods_list[0]

def on_sidebar_change():
    st.session_state.selected_period = st.session_state.capsule_native_key

def on_hidden_capsule_change():
    st.session_state.selected_period = st.session_state.capsule_hidden_key

# ==========================================
# 3. 🎛️ 左側控制台開發 (包含雙重清洗引擎與智能微調)
# ==========================================
with st.sidebar:
    st.markdown("## 🎛️ TTPush 運維控制台")
    st.caption("台東金幣大數據自動化清洗引擎 v8.5")
    st.markdown("---")
    
    st.markdown("#### 📅 歷史週報快速檢視")
    st.selectbox(
        "請選擇欲調閱的營業週間：",
        options=historical_periods_list,
        index=historical_periods_list.index(st.session_state.selected_period),
        key="capsule_native_key",
        on_change=on_sidebar_change,
        label_visibility="collapsed"
    )
    st.info(f"💡 目前戰情室正定錨在：\n`{st.session_state.selected_period}`")
    st.markdown("---")
    
    # ------------------------------------------
    # 舊版歷史報表單檔上傳區塊
    # ------------------------------------------
    st.markdown("#### ⏳ 舊版報表批次上傳 (單檔)")
    uploaded_files = st.file_uploader(
        "支援多份舊版 CSV 報表同時拖放：", 
        type=["csv"], 
        accept_multiple_files=True,
        key="uploader_pipeline"
    )
    
    if uploaded_files:
        db_updated = False
        total_files = len(uploaded_files)
        progress_bar = st.progress(0, text="準備啟動深度特徵碼清洗管線...")
        
        for idx, file in enumerate(uploaded_files):
            try:
                progress_bar.progress((idx + 1) / total_files, text=f"正在彈性模糊掃描全網格: {file.name}")
                time.sleep(0.1)
                
                with open(BAK_FILE, "w", encoding="utf-8") as bak_f:
                    json.dump(DATA_ENGINE, bak_f, ensure_ascii=False, indent=4)
                    
                raw_df = pd.read_csv(file, header=None).fillna("")
                p_key = None
                
                parsed_k1 = {"actual_total_users": 0, "derived_weekly_new_users": 0, "total_push_accumulated": 0, "weekly_push_current": 0}
                parsed_k2 = {"weekly_coins_issued": 0, "weekly_coins_redeemed_audited": 0, "active_stores_count": 0, "new_stores_adjusted": 0, "total_accumulated_coins": 0, "total_stores_accumulated": 0}
                parsed_k3 = {"b110": "176,839,060", "b111": "67,113,280", "b112": "66,302,010", "b113": "104,541,785", "b114": "82,390,693", "b115": "78,941,000"}
                parsed_k4 = {"expire_20260930_coins": 0, "expire_20270930_coins": 0}
                
                for idx_row, row in raw_df.iterrows():
                    cells = [str(c).strip() for c in row if str(c).strip()]
                    row_joined = "||".join(cells)
                    
                    if "更新區間" in row_joined:
                        for c in cells:
                            if "/" in c and "-" in c:
                                p_key = f"統計區間：{c.replace('-', ' — ')}"
                    
                    if "累積會員數" in row_joined:
                        for c in cells:
                            if "/" in c and "人" in c:
                                t_part, w_part = c.split('/')
                                parsed_k1["actual_total_users"] = int(t_part.replace('人','').replace(',','').strip())
                                parsed_k1["derived_weekly_new_users"] = int(w_part.replace('人','').replace(',','').strip())
                    
                    if "發送則數" in row_joined or "推播則數" in row_joined:
                        for c in cells:
                            if "/" in c and "則" in c:
                                tp_part, wp_part = c.split('/')
                                parsed_k1["total_push_accumulated"] = int(tp_part.replace('則','').replace(',','').strip())
                                parsed_k1["weekly_push_current"] = int(wp_part.replace('則','').replace(',','').strip())
                    
                    if "發放金幣數" in row_joined:
                        for c in cells:
                            if "枚" in c and "/" not in c:
                                parsed_k2["weekly_coins_issued"] = int(c.replace('枚','').replace(',','').strip())
                    if "兌換金幣數" in row_joined:
                        for c in cells:
                            if "枚" in c and "/" not in c:
                                parsed_k2["weekly_coins_redeemed_audited"] = int(c.replace('枚','').replace(',','').strip())
                    
                    if "消費店家數" in row_joined:
                        for c in cells:
                            if "/" in c and "家" in c:
                                try:
                                    as_part, ns_part = c.split('/')
                                    as_clean = as_part.replace('家','').replace(',','').replace('+','').strip()
                                    ns_clean = ns_part.replace('家','').replace(',','').replace('+','').strip()
                                    parsed_k2["active_stores_count"] = int(as_clean)
                                    parsed_k2["new_stores_adjusted"] = int(ns_clean)
                                    break
                                except Exception:
                                    pass

                    if "總特約店家數" in row_joined or "簽約之特約店家" in row_joined:
                        for c in cells:
                            if "家" in c and "/" not in c:
                                try:
                                    ts_clean = c.replace('家','').replace(',','').replace('+','').strip()
                                    parsed_k2["total_stores_accumulated"] = int(ts_clean)
                                    break
                                except Exception:
                                    pass
                            elif "/" in c and "家" in c:
                                try:
                                    _, ts_part = c.split('/')
                                    ts_clean = ts_part.replace('家','').replace(',','').replace('+','').strip()
                                    parsed_k2["total_stores_accumulated"] = int(ts_clean)
                                    break
                                except Exception:
                                    pass
                                
                    if "累積發放金幣數" in row_joined:
                        for c in cells:
                            if "枚" in c and "/" not in c:
                                parsed_k2["total_accumulated_coins"] = int(c.replace('枚','').replace(',','').strip())

                    if "115年度預算" in row_joined or "17期" in row_joined:
                        for c in cells:
                            if "枚" in c:
                                parsed_k3["b115"] = c.replace('枚','').replace(',','').strip()

                    if "2026/09/30" in row_joined or "2026/9/30" in row_joined:
                        for c in cells:
                            if "枚" in c:
                                parsed_k4["expire_20260930_coins"] = int(c.replace('枚','').replace(',','').strip())
                    if "2027/09/30" in row_joined or "2027/9/30" in row_joined:
                        for c in cells:
                            if "枚" in c:
                                parsed_k4["expire_20270930_coins"] = int(c.replace('枚','').replace(',','').strip())
                
                if p_key:
                    DATA_ENGINE[p_key] = {"k1_metrics": parsed_k1, "k2_metrics": parsed_k2, "k3_metrics": parsed_k3, "k4_metrics": parsed_k4}
                    db_updated = True
                    st.toast(f"自動清洗完畢：{p_key}", icon="📊")
            except Exception as e:
                st.error(f"解析 {file.name} 失敗: {e}")
        
        if db_updated:
            with open(JSON_FILE, "w", encoding="utf-8") as f:
                json.dump(DATA_ENGINE, f, ensure_ascii=False, indent=4)
            progress_bar.progress(100, text="🎉 歷史資料庫高階數據全同步完成！")
            time.sleep(0.5)
            st.cache_data.clear()
            st.rerun()

    st.markdown("---")
    
    # ------------------------------------------
    # 🌟 [全新] 新版雙表合併解析區 (支援 CSV 與 Excel，無單位限制版)
    # ------------------------------------------
    st.markdown("#### ✨ [新版] 雙表合併自動解析")
    new_files = st.file_uploader(
        "請同時拖曳本週的「綜合報表」與「交易紀錄」：", 
        type=["csv", "xlsx", "xls"], 
        accept_multiple_files=True,
        key="new_format_uploader"
    )

    if new_files and len(new_files) > 0:
        if st.button("🚀 啟動雙表對齊與繼承計算", use_container_width=True):
            report_df = None
            txn_df = None
            
            for f in new_files:
                is_excel = f.name.endswith(('.xlsx', '.xls'))
                if "報表" in f.name:
                    report_df = pd.read_excel(f, header=None).fillna("") if is_excel else pd.read_csv(f, header=None).fillna("")
                elif "交易" in f.name:
                    txn_df = pd.read_excel(f).fillna("") if is_excel else pd.read_csv(f).fillna("")
            
            if report_df is not None and txn_df is not None:
                try:
                    # 2. 提煉變動數據
                    new_users, new_stores, issued, redeemed = 0, 0, 0, 0
                    exp26_parsed, exp27_parsed = None, None
                    
                    for _, row in report_df.iterrows():
                        col0 = str(row[0]).strip()
                        col1 = str(row[1]).strip()
                        
                        if col0 == "新增會員數" and col1.isdigit(): new_users = int(col1)
                        elif col0 == "新增特約店家數" and col1.isdigit(): new_stores = int(col1)
                        elif col0 == "總金幣發放枚數" and col1.isdigit(): issued = int(col1)
                        elif col0 == "民眾使用情況" and col1.isdigit(): redeemed = int(col1)
                        
                        # 🎯 進化版：不管有沒有「枚」字，只要同行有該日期，就自動萃取最大的純數字
                        row_str = "||".join([str(c) for c in row])
                        
                        if "2026/09/30" in row_str or "2026/9/30" in row_str:
                            for c in row:
                                clean_c = str(c).replace('枚','').replace(',','').strip()
                                if clean_c.isdigit():
                                    exp26_parsed = int(clean_c)
                                    
                        if "2027/09/30" in row_str or "2027/9/30" in row_str:
                            for c in row:
                                clean_c = str(c).replace('枚','').replace(',','').strip()
                                if clean_c.isdigit():
                                    exp27_parsed = int(clean_c)
                    
                    # 3. 從明細表提煉活躍店家與動態日期
                    active_stores = txn_df["商家名稱"].nunique() if "商家名稱" in txn_df.columns else 0
                    
                    if "交易時間" in txn_df.columns:
                        txn_df["交易時間"] = pd.to_datetime(txn_df["交易時間"])
                        min_date = txn_df["交易時間"].min()
                        max_date = txn_df["交易時間"].max()
                        tw_min_y = min_date.year - 1911
                        tw_max_y = max_date.year - 1911
                        period_key = f"統計區間：{tw_min_y}/{min_date.strftime('%m/%d')} — {tw_max_y}/{max_date.strftime('%m/%d')}"
                    else:
                        period_key = "統計區間：115/05/29 — 115/06/04"
                    
                    # 4. 繼承歷史推算
                    last_period = historical_periods_list[0]
                    prev_data = DATA_ENGINE.get(last_period, {})
                    
                    prev_k1 = prev_data.get("k1_metrics", {})
                    prev_k2 = prev_data.get("k2_metrics", {})
                    prev_k3 = prev_data.get("k3_metrics", {})
                    prev_k4 = prev_data.get("k4_metrics", {})
                    
                    act_total_users = int(prev_k1.get("actual_total_users", 0)) + new_users
                    act_total_stores = int(prev_k2.get("total_stores_accumulated", 679)) + new_stores
                    act_total_coins = int(prev_k2.get("total_accumulated_coins", 0)) + issued
                    
                    # 處理到期金幣：如果有抓到就用新的，沒抓到就繼承上週
                    final_exp26 = exp26_parsed if exp26_parsed is not None else int(prev_k4.get("expire_20260930_coins", 0))
                    final_exp27 = exp27_parsed if exp27_parsed is not None else int(prev_k4.get("expire_20270930_coins", 0))
                    
                    # 5. 組裝全新一週的 JSON 並寫入
                    DATA_ENGINE[period_key] = {
                        "k1_metrics": {
                            "actual_total_users": act_total_users,
                            "derived_weekly_new_users": new_users,
                            "total_push_accumulated": int(prev_k1.get("total_push_accumulated", 6465)),
                            "weekly_push_current": 0
                        },
                        "k2_metrics": {
                            "weekly_coins_issued": issued,
                            "weekly_coins_redeemed_audited": redeemed,
                            "active_stores_count": active_stores,
                            "new_stores_adjusted": new_stores,
                            "total_accumulated_coins": act_total_coins,
                            "total_stores_accumulated": act_total_stores
                        },
                        "k3_metrics": prev_k3,
                        "k4_metrics": {
                            "expire_20260930_coins": final_exp26,
                            "expire_20270930_coins": final_exp27
                        }
                    }
                    
                    with open(BAK_FILE, "w", encoding="utf-8") as bak_f:
                        json.dump(DATA_ENGINE, bak_f, ensure_ascii=False, indent=4)
                    with open(JSON_FILE, "w", encoding="utf-8") as f:
                        json.dump(DATA_ENGINE, f, ensure_ascii=False, indent=4)
                        
                    st.success(f"✅ 成功洗入新資料：{period_key}")
                    st.session_state.selected_period = period_key
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"解析失敗: {e}")
            else:
                st.warning("⚠️ 請務必「同時」上傳【報表】與【會員交易紀錄】兩個檔案喔！")

    st.markdown("---")

    # ------------------------------------------
    # 🌟 [全新] 手動數據微調面板 (加入推播智能相加公式與雙欄排版)
    # ------------------------------------------
    st.markdown("#### ✏️ 手動數據微調")
    with st.expander("點此展開微調面板", expanded=False):
        cur_data = DATA_ENGINE.get(st.session_state.selected_period, {})
        cur_k1 = cur_data.get("k1_metrics", {})
        cur_k2 = cur_data.get("k2_metrics", {})
        cur_k4 = cur_data.get("k4_metrics", {})
        
        with st.form("manual_override_form"):
            st.caption(f"目前修改區間：\n{st.session_state.selected_period}")
            
            # 採用雙欄設計：左邊為本週新增，右邊為累積總數
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                new_w_push = st.number_input("🚀 本週推播則數", value=int(cur_k1.get("weekly_push_current", 0)), step=1)
            with col_p2:
                new_t_push = st.number_input("📣 總累積推播數", value=int(cur_k1.get("total_push_accumulated", 6465)), step=1)

            col_u1, col_u2 = st.columns(2)
            with col_u1:
                new_w_users = st.number_input("👤 本週新增會員", value=int(cur_k1.get("derived_weekly_new_users", 0)), step=1)
            with col_u2:
                new_t_users = st.number_input("👥 總累積會員數", value=int(cur_k1.get("actual_total_users", 0)), step=1)
            
            st.markdown("---")
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                new_w_stores = st.number_input("📈 本週新增店家", value=int(cur_k2.get("new_stores_adjusted", 0)), step=1)
            with col_s2:
                new_t_stores = st.number_input("🏪 總特約店家數", value=int(cur_k2.get("total_stores_accumulated", 0)), step=1)
            
            st.markdown("---")
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                new_exp26 = st.number_input("⏳ 2026到期金幣", value=int(cur_k4.get("expire_20260930_coins", 0)), step=1)
            with col_e2:
                new_exp27 = st.number_input("⏳ 2027到期金幣", value=int(cur_k4.get("expire_20270930_coins", 0)), step=1)
            
            submit_override = st.form_submit_button("💾 儲存並自動計算總和")
            
            if submit_override:
                if st.session_state.selected_period not in DATA_ENGINE:
                    DATA_ENGINE[st.session_state.selected_period] = {"k1_metrics": {}, "k2_metrics": {}, "k3_metrics": {}, "k4_metrics": {}}
                
                # 💡 智能相加公式：抓取上一期的歷史資料
                idx = historical_periods_list.index(st.session_state.selected_period)
                prev_period_key = historical_periods_list[idx + 1] if idx + 1 < len(historical_periods_list) else None
                prev_data_ref = DATA_ENGINE.get(prev_period_key, {}) if prev_period_key else {}
                
                # [推播] 如果您改了本週推播，且沒有手動去改總推播，系統自動幫您加上去！
                orig_w_push = int(cur_k1.get("weekly_push_current", 0))
                if new_w_push != orig_w_push and new_t_push == int(cur_k1.get("total_push_accumulated", 6465)):
                    prev_t = int(prev_data_ref.get("k1_metrics", {}).get("total_push_accumulated", 6465))
                    new_t_push = prev_t + new_w_push
                    
                # [會員] 智能相加
                orig_w_users = int(cur_k1.get("derived_weekly_new_users", 0))
                if new_w_users != orig_w_users and new_t_users == int(cur_k1.get("actual_total_users", 0)):
                    prev_t = int(prev_data_ref.get("k1_metrics", {}).get("actual_total_users", 0))
                    new_t_users = prev_t + new_w_users
                    
                # [店家] 智能相加
                orig_w_stores = int(cur_k2.get("new_stores_adjusted", 0))
                if new_w_stores != orig_w_stores and new_t_stores == int(cur_k2.get("total_stores_accumulated", 0)):
                    prev_t = int(prev_data_ref.get("k2_metrics", {}).get("total_stores_accumulated", 0))
                    new_t_stores = prev_t + new_w_stores
                
                # 寫入覆蓋
                DATA_ENGINE[st.session_state.selected_period]["k1_metrics"]["weekly_push_current"] = new_w_push
                DATA_ENGINE[st.session_state.selected_period]["k1_metrics"]["total_push_accumulated"] = new_t_push
                DATA_ENGINE[st.session_state.selected_period]["k1_metrics"]["derived_weekly_new_users"] = new_w_users
                DATA_ENGINE[st.session_state.selected_period]["k1_metrics"]["actual_total_users"] = new_t_users
                
                DATA_ENGINE[st.session_state.selected_period]["k2_metrics"]["new_stores_adjusted"] = new_w_stores
                DATA_ENGINE[st.session_state.selected_period]["k2_metrics"]["total_stores_accumulated"] = new_t_stores
                
                DATA_ENGINE[st.session_state.selected_period]["k4_metrics"]["expire_20260930_coins"] = new_exp26
                DATA_ENGINE[st.session_state.selected_period]["k4_metrics"]["expire_20270930_coins"] = new_exp27
                
                with open(JSON_FILE, "w", encoding="utf-8") as f:
                    json.dump(DATA_ENGINE, f, ensure_ascii=False, indent=4)
                
                st.success("✅ 數據已更新並完成智能相加！")
                time.sleep(0.5)
                st.rerun()

    st.markdown("---")
    
    # ------------------------------------------
    # 🌟 [全新] Excel 資料匯出引擎
    # ------------------------------------------
    st.markdown("#### 📥 歷史數據匯出")
    
    # 將 JSON 大腦的資料扁平化並轉成 DataFrame
    export_records = []
    for period, data in DATA_ENGINE.items():
        row = {"統計區間": period}
        row.update(data.get("k1_metrics", {}))
        row.update(data.get("k2_metrics", {}))
        row.update(data.get("k4_metrics", {}))
        export_records.append(row)
        
    if export_records:
        df_export = pd.DataFrame(export_records)
        
        # 將工程英文變數，翻譯成長官看得懂的中文欄位
        rename_mapping = {
            "actual_total_users": "累積會員總數",
            "derived_weekly_new_users": "本週新增會員",
            "total_push_accumulated": "累計推播則數",
            "weekly_push_current": "本週推播則數",
            "weekly_coins_issued": "當週發放金幣",
            "weekly_coins_redeemed_audited": "當週兌換金幣",
            "active_stores_count": "消費店家數",
            "new_stores_adjusted": "新增店家數",
            "total_accumulated_coins": "臺東金幣總發放數",
            "total_stores_accumulated": "總特約店家數",
            "expire_20260930_coins": "2026到期金幣餘額",
            "expire_20270930_coins": "2027到期金幣餘額"
        }
        df_export = df_export.rename(columns=rename_mapping)
        
        # 在記憶體中將表格轉為 Excel 格式
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_export.to_excel(writer, index=False, sheet_name='TTPush戰情室歷史數據')
        output.seek(0)
        
        # 產生下載按鈕
        today_str = datetime.datetime.now().strftime("%Y%m%d")
        st.download_button(
            label="📥 下載全歷史 Excel 報表",
            data=output,
            file_name=f"TTPush_戰情室數據匯出_{today_str}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    st.markdown("---")
    st.markdown("#### ⚙️ 資料庫安全閘門")
    col_bak, col_rst = st.columns(2)
    with col_bak:
        if st.button("💾 手動備份", use_container_width=True):
            with open(BAK_FILE, "w", encoding="utf-8") as bak_f:
                json.dump(DATA_ENGINE, bak_f, ensure_ascii=False, indent=4)
            st.sidebar.success("備份完畢")
    with col_rst:
        if st.button("⏪ 一鍵還原", use_container_width=True):
            if os.path.exists(BAK_FILE):
                with open(BAK_FILE, "r", encoding="utf-8") as bak_f:
                    restored_data = json.load(bak_f)
                with open(JSON_FILE, "w", encoding="utf-8") as f:
                    json.dump(restored_data, f, ensure_ascii=False, indent=4)
                st.sidebar.warning("已還原歷史紀錄！")
                time.sleep(0.5)
                st.rerun()

# ==========================================
# 4. 前台頁面渲染與雙主鍵定死融合
# ==========================================
html_title = '<div class="fixed-title">TTPush週營運資料統計分析</div>'
st.markdown(html_title, unsafe_allow_html=True)

html_capsule = f'<div class="capsule-visual-container"><div class="morandi-static-capsule">{st.session_state.selected_period}</div></div>'
st.markdown(html_capsule, unsafe_allow_html=True)

st.selectbox(
    "隱形控制核心",
    options=historical_periods_list,
    index=historical_periods_list.index(st.session_state.selected_period),
    label_visibility="collapsed",
    key="capsule_hidden_key",
    on_change=on_hidden_capsule_change
)

selected_period = st.session_state.selected_period
metrics = DATA_ENGINE.get(selected_period, {
    "k1_metrics": {"actual_total_users": 0, "derived_weekly_new_users": 0, "total_push_accumulated": 0, "weekly_push_current": 0},
    "k2_metrics": {"weekly_coins_issued": 0, "weekly_coins_redeemed_audited": 0, "active_stores_count": 0, "new_stores_adjusted": 0, "total_accumulated_coins": 0, "total_stores_accumulated": 679},
    "k3_metrics": {"b110": "176,839,060", "b111": "67,113,280", "b112": "66,302,010", "b113": "104,541,785", "b114": "82,390,693", "b115": "78,941,000"},
    "k4_metrics": {"expire_20260930_coins": 0, "expire_20270930_coins": 0}
})

k1_d = metrics.get("k1_metrics", {})
k2_d = metrics.get("k2_metrics", {})
k3_d = metrics.get("k3_metrics", {"b110": "176,839,060", "b111": "67,113,280", "b112": "66,302,010", "b113": "104,541,785", "b114": "82,390,693", "b115": "78,941,000"})
k4_d = metrics.get("k4_metrics", {})

# ==========================================
# 變數抽取區
# ==========================================
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

# ==========================================
# 四欄佈局與渲染
# ==========================================
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