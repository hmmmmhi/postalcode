import streamlit as st
import pandas as pd
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import pgeocode

# ページ設定
st.set_page_config(page_title="複数病院の距離計算アプリ", layout="wide")
st.title("🏥 複数の病院からの距離を計算するアプリ")

# 緯度経度を取得する関数
@st.cache_data(show_spinner=False)
def get_coordinates_by_name(name):
    geolocator = Nominatim(user_agent="distance_app")
    location = geolocator.geocode(name)
    if location:
        return (location.latitude, location.longitude)
    return None

# 郵便番号から座標を取得（pgeocode使用）
@st.cache_data(show_spinner=False)
def get_coordinates_by_postal(postal):
    nomi = pgeocode.Nominatim('jp')
    result = nomi.query_postal_code(str(postal).replace("-", ""))
    if pd.notna(result.latitude) and pd.notna(result.longitude):
        return (result.latitude, result.longitude)
    return None

# 病院名の入力（最大10件）
st.header("① 複数の病院名または住所を入力してください（最大10件）")
hospital_names = []
for i in range(1, 11):
    name = st.text_input(f"病院{i}：", value="" if i > 1 else "京都大学医学部附属病院")
    if name:
        hospital_names.append(name)

hospital_coords = {}
for name in hospital_names:
    coord = get_coordinates_by_name(name)
    if coord:
        hospital_coords[name] = coord
    else:
        st.warning(f"「{name}」の座標が取得できませんでした。")

# ファイルのアップロード（CSVまたはExcel）
st.header("② 郵便番号データのファイルをアップロード")
uploaded_file = st.file_uploader("CSVまたはExcelファイルを選択してください", type=["csv", "xlsx"])

if uploaded_file:
    # ファイル読み込み
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file, engine="openpyxl")
    except Exception as e:
        st.error(f"ファイルの読み込み中にエラーが発生しました：{e}")
        st.stop()

    st.write("アップロードされたデータ（先頭5行）：")
    st.dataframe(df.head())

    # 郵便番号列を選択
    postal_col = st.selectbox("郵便番号が記載された列を選んでください", df.columns)

    # 各行について、病院ごとの距離を計算
    for hosp_name, hosp_coord in hospital_coords.items():
        distances = []
        for code in df[postal_col]:
            user_coord = get_coordinates_by_postal(code)
            if user_coord:
                dist = geodesic(hosp_coord, user_coord).km
            else:
                dist = None
            distances.append(dist)
        df[f"{hosp_name}までの距離(km)"] = distances

    st.header("③ 距離計算の結果")
    st.dataframe(df)

    # ダウンロード用ファイル作成
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 結果をCSVでダウンロード", csv, "distance_result.csv", "text/csv")
