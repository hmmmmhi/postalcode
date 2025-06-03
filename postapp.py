import streamlit as st
import pandas as pd
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import pgeocode

# ページ設定
st.set_page_config(page_title="病院からの距離計算アプリ", layout="centered")
st.title("🏥 病院名をもとに距離を計算するアプリ")

# 基準地点の入力
st.header("① 病院名または住所を入力してください")
hospital_name = st.text_input("例：京都大学医学部附属病院", value="京都大学医学部附属病院")

# 住所から緯度経度を取得する関数
@st.cache_data(show_spinner=False)
def get_location_by_name(name):
    geolocator = Nominatim(user_agent="distance_app")
    location = geolocator.geocode(name)
    if location:
        return (location.latitude, location.longitude)
    return None

base_coords = get_location_by_name(hospital_name)

if base_coords is None:
    st.error("病院名または住所が正しく認識できませんでした。")
else:
    st.success(f"基準地点の緯度経度: {base_coords}")

    # ファイルアップロード
    st.header("② 郵便番号が含まれるファイルをアップロード（ExcelまたはCSV）")
    uploaded_file = st.file_uploader("ファイルを選択してください", type=["csv", "xlsx"])

    if uploaded_file:
        # ファイル形式に応じて読み込み
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.write("アップロードされたデータのプレビュー：")
        st.dataframe(df.head())

        # 郵便番号列の選択
        postal_col = st.selectbox("郵便番号の列を選択してください", df.columns)

        # 郵便番号 → 緯度経度
        nomi = pgeocode.Nominatim('jp')

        distances = []
        for code in df[postal_col]:
            result = nomi.query_postal_code(str(code).replace("-", ""))
            if pd.notna(result.latitude) and pd.notna(result.longitude):
                coord = (result.latitude, result.longitude)
                distance_km = geodesic(base_coords, coord).km
            else:
                distance_km = None
            distances.append(distance_km)

        df["距離(km)"] = distances

        st.header("③ 距離計算の結果")
        st.dataframe(df)

        # ダウンロード用CSV
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 結果をCSVでダウンロード", csv, "distance_result.csv", "text/csv")
