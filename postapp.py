import streamlit as st
import pandas as pd
import googlemaps
import re

# --------------------------
# ページ設定
# --------------------------
st.set_page_config(page_title="電車距離計算アプリ", layout="wide")
st.title("🚃 郵便番号から電車距離と所要時間を計算（Google Maps API）")

# --------------------------
# ① APIキーの読み込み
# --------------------------
st.header("① Google Maps APIキーをアップロード")
api_file = st.file_uploader("1行目にAPIキーを記載した .txt ファイルをアップロード", type="txt")

if not api_file:
    st.warning("APIキーが必要です。アップロードしてください。")
    st.stop()

try:
    api_key = api_file.readline().decode("utf-8").strip()
    gmaps = googlemaps.Client(key=api_key)
    st.success("✅ APIキーを読み込みました。")
except Exception as e:
    st.error(f"APIキーの読み込みに失敗しました：{e}")
    st.stop()

# --------------------------
# ② 病院名の入力（最大10件）
# --------------------------
st.header("② 病院名を入力（最大10件）")
default_hospitals = [
    "医仁会武田病院", "宇治武田病院", "康生会武田病院",
    "京都桂病院", "堀川病院", "大津日赤病院"
]
hospital_names = []
for i in range(10):
    default = default_hospitals[i] if i < len(default_hospitals) else ""
    name = st.text_input(f"病院{i+1}", value=default)
    if name:
        hospital_names.append(name)

# --------------------------
# ③ ファイルアップロード
# --------------------------
st.header("③ 郵便番号を含むCSVまたはExcelファイルをアップロード")
uploaded_file = st.file_uploader("CSVまたはExcelファイル", type=["csv", "xlsx"])

if not uploaded_file:
    st.stop()

try:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file, engine="openpyxl")
except Exception as e:
    st.error(f"ファイルの読み込みに失敗しました：{e}")
    st.stop()

st.write("アップロードされたデータ（先頭5行）:")
st.dataframe(df.head())

# --------------------------
# ④ 郵便番号列の選択と住所変換
# --------------------------
postal_col = st.selectbox("郵便番号の列を選んでください", df.columns)

def get_address_from_postal(gmaps, postal_code):
    try:
        query = f"{postal_code} 日本"
        result = gmaps.geocode(query)
        if result and "formatted_address" in result[0]:
            return result[0]["formatted_address"]
        else:
            return None
    except Exception:
        return None

addresses = []
for code in df[postal_col]:
    try:
        if pd.isna(code):
            addresses.append(None)
            continue
        code_str = re.sub(r"[^\d]", "", str(code))  # ハイフン・空白除去
        if len(code_str) != 7:
            addresses.append(None)
            continue
        addr = get_address_from_postal(gmaps, code_str)
        addresses.append(addr)
    except:
        addresses.append(None)

df["住所"] = addresses
st.write("変換された住所（先頭5行）:")
st.write(df[["住所"]].head())

# --------------------------
# ⑤ 距離と時間の計算（電車）
# --------------------------
st.header("⑤ 病院ごとの電車ルート距離と所要時間を計算")

for hosp in hospital_names:
    dist_list = []
    time_list = []

    for origin in df["住所"]:
        if not origin:
            dist_list.append(None)
            time_list.append(None)
            continue

        try:
            directions = gmaps.directions(
                origin=origin,
                destination=hosp,
                mode="transit",
                language="ja",
                departure_time="now"
            )
            if not directions:
                dist_km = None
                time_min = None
            else:
                leg = directions[0]["legs"][0]
                dist_km = round(leg["distance"]["value"] / 1000, 2)
                time_min = round(leg["duration"]["value"] / 60)
        except:
            dist_km = None
            time_min = None

        dist_list.append(dist_km)
        time_list.append(time_min)

    df[f"{hosp}までの距離(km)"] = dist_list
    df[f"{hosp}までの時間(min)"] = time_list

# --------------------------
# ⑥ 結果表示とダウンロード
# --------------------------
st.header("⑥ 計算結果の表示とCSVダウンロード")
st.dataframe(df)

csv = df.to_csv(index=False).encode("utf-8-sig")
st.download_button("📥 結果をCSVでダウンロード", csv, "電車距離計算結果.csv", "text/csv")
