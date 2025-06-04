import streamlit as st
import pandas as pd
import googlemaps
import re

# -------------------------
# ページ初期設定
# -------------------------
st.set_page_config(page_title="電車距離計算アプリ", layout="wide")
st.title("郵便番号から公共交通での距離・時間を計算（Google Maps API）")

# -------------------------
# 1. APIキーの読み込み
# -------------------------
st.header("① Google Maps APIキーをアップロード")
api_file = st.file_uploader("APIキー（1行目）を含む.txtファイル", type="txt")

if not api_file:
    st.warning("APIキーをアップロードしてください。")
    st.stop()

try:
    api_key = api_file.readline().decode("utf-8").strip()
    gmaps = googlemaps.Client(key=api_key)
    st.success("✅ APIキーを読み込みました。")
except Exception as e:
    st.error(f"APIキーの読み込みに失敗しました：{e}")
    st.stop()

# -------------------------
# 2. 病院名の入力（最大10件）
# -------------------------
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

# -------------------------
# 3. ファイルアップロード
# -------------------------
st.header("③ 郵便番号を含むCSVまたはExcelファイルをアップロード")
uploaded_file = st.file_uploader("ファイルを選択（CSVまたはExcel）", type=["csv", "xlsx"])

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

st.write("アップロードされたデータ：")
st.dataframe(df.head())

# -------------------------
# 4. 郵便番号から緯度経度を取得
# -------------------------
st.header("④ 郵便番号から緯度・経度を取得（Geocoding API）")

postal_col = st.selectbox("郵便番号の列を選んでください", df.columns)

def get_latlng_from_postal(postal_code):
    try:
        query = f"{postal_code}, Japan"
        result = gmaps.geocode(query)
        if result and "geometry" in result[0]:
            loc = result[0]["geometry"]["location"]
            return (loc["lat"], loc["lng"])
        else:
            return None
    except Exception:
        return None

latlngs = []
for code in df[postal_col]:
    if pd.isna(code):
        latlngs.append(None)
        continue
    code_str = str(code).strip()
    if not re.match(r"^\d{3}-\d{4}$", code_str):
        latlngs.append(None)
        continue
    latlng = get_latlng_from_postal(code_str)
    latlngs.append(latlng)

df["緯度経度"] = latlngs
st.write("取得された緯度・経度：")
st.write(df[["緯度経度"]].head())

# -------------------------
# 5. Directions APIで距離と時間計算
# -------------------------
st.header("⑤ 病院ごとの距離・所要時間（公共交通）を計算")

for hosp in hospital_names:
    dist_list = []
    time_list = []

    for origin_coord in df["緯度経度"]:
        if not origin_coord:
            dist_list.append(None)
            time_list.append(None)
            continue

        try:
            directions = gmaps.directions(
                origin=origin_coord,
                destination=hosp,
                mode="transit",
                language="ja"
            )
            if not directions:
                dist_km = None
                time_min = None
            else:
                leg = directions[0]["legs"][0]
                dist_km = round(leg["distance"]["value"] / 1000, 2)
                time_min = round(leg["duration"]["value"] / 60)
        except Exception:
            dist_km = None
            time_min = None

        dist_list.append(dist_km)
        time_list.append(time_min)

    df[f"{hosp}までの距離(km)"] = dist_list
    df[f"{hosp}までの時間(min)"] = time_list

# -------------------------
# 6. 結果表示とCSVダウンロード
# -------------------------
st.header("⑥ 計算結果")
st.dataframe(df)

csv = df.to_csv(index=False).encode("utf-8-sig")
st.download_button("📥 結果をCSVでダウンロード", csv, "distance_result.csv", "text/csv")
