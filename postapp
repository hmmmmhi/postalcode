import streamlit as st
import pandas as pd
from geopy.distance import geodesic
import pgeocode

# ページ設定
st.set_page_config(page_title="郵便番号 距離計算アプリ", layout="centered")

st.title("📍 郵便番号から距離を算出するアプリ")

# 基準地点（手入力または緯度経度指定）
st.header("① 基準地点を設定してください")
base_postal = st.text_input("基準の郵便番号（例：604-8471）", value="604-8471")

# 郵便番号 → 緯度経度に変換する関数
def get_coordinates(postal_code):
    nomi = pgeocode.Nominatim('jp')
    result = nomi.query_postal_code(postal_code.replace("-", ""))
    if pd.isna(result.latitude) or pd.isna(result.longitude):
        return None
    return (result.latitude, result.longitude)

base_coords = get_coordinates(base_postal)

if base_coords is None:
    st.error("基準郵便番号が正しくありません。")
else:
    st.success(f"基準地点の緯度経度: {base_coords}")

    # ファイルアップロード
    st.header("② 郵便番号が含まれるファイルをアップロード")
    uploaded_file = st.file_uploader("CSVファイルを選択してください（郵便番号列が必要です）", type="csv")

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write("アップロードされたデータのプレビュー：")
        st.dataframe(df.head())

        # 郵便番号列の選択
        postal_col = st.selectbox("郵便番号の列を選択してください", df.columns)

        # 距離計算
        distances = []
        for code in df[postal_col]:
            coords = get_coordinates(str(code))
            if coords:
                distance_km = geodesic(base_coords, coords).km
            else:
                distance_km = None
            distances.append(distance_km)

        df["距離(km)"] = distances
        st.header("③ 距離計算の結果")
        st.dataframe(df)

        # ダウンロードリンク作成
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 結果をCSVでダウンロード", csv, "distance_result.csv", "text/csv")
