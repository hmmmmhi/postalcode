import streamlit as st
import pandas as pd
import googlemaps
import pgeocode
import io

# ページ設定
st.set_page_config(page_title="Google Maps 距離計算アプリ", layout="wide")
st.title("🏥 Google Maps APIで病院までの距離と時間を算出")

# ① APIキーファイルのアップロード
st.header("① Google Maps APIキーをアップロードしてください（.txtファイル、1行目にAPIキー）")
api_file = st.file_uploader("APIキー（TXTファイル）", type="txt")

if api_file:
    try:
        api_key = api_file.readline().decode("utf-8").strip()
        gmaps = googlemaps.Client(key=api_key)
        st.success("APIキーを読み込みました。")
    except Exception as e:
        st.error(f"APIキーの読み込みに失敗しました: {e}")
        st.stop()
else:
    st.info("APIキーのアップロードをお待ちしています。")
    st.stop()

# ② 病院名の入力
st.header("② 病院名または住所を入力（最大10件、初期値6件）")
default_hospitals = [
    "医仁会武田病院",
    "宇治武田病院",
    "康生会武田病院",
    "京都桂病院",
    "堀川病院",
    "大津日赤病院"
]
hospital_names = []
for i in range(10):
    default = default_hospitals[i] if i < len(default_hospitals) else ""
    name = st.text_input(f"病院{i+1}", value=default)
    if name:
        hospital_names.append(name)

# ③ データファイルアップロード
st.header("③ 郵便番号付きのCSVまたはExcelファイルをアップロード")
uploaded_file = st.file_uploader("CSVまたはExcelファイル", type=["csv", "xlsx"])

if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file, engine="openpyxl")
    except Exception as e:
        st.error(f"ファイルの読み込みに失敗しました：{e}")
        st.stop()

    st.write("アップロードされたデータのプレビュー：")
    st.dataframe(df.head())

    # 郵便番号列の指定
    postal_col = st.selectbox("郵便番号が記載された列を選んでください", df.columns)

    # 郵便番号 → 住所変換
    nomi = pgeocode.Nominatim("jp")
    addresses = []
    for code in df[postal_col]:
        code_str = str(code).replace("-", "").strip()
        query = nomi.query_postal_code(code_str)
        if pd.notna(query.place_name):
            addr = f"{query.prefecture_name}{query.place_name}"
        else:
            addr = None
        addresses.append(addr)
    df["住所"] = addresses

    # 距離と時間の計算
    for hosp in hospital_names:
        dist_list = []
        time_list = []
        for addr in df["住所"]:
            if addr is None:
                dist_km = None
                time_min = None
            else:
                try:
                    directions = gmaps.directions(
                        origin=addr,
                        destination=hosp,
                        mode="driving",  # 'walking', 'transit', 'bicycling'も選べます
                        language="ja"
                    )
                    leg = directions[0]['legs'][0]
                    dist_km = round(leg['distance']['value'] / 1000, 2)
                    time_min = round(leg['duration']['value'] / 60)
                except:
                    dist_km = None
                    time_min = None
            dist_list.append(dist_km)
            time_list.append(time_min)
        df[f"{hosp}までの距離(km)"] = dist_list
        df[f"{hosp}までの所要時間(min)"] = time_list

    st.header("④ 距離と時間の計算結果")
    st.dataframe(df)

    # ダウンロード
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 結果をCSVでダウンロード", csv, "distance_results.csv", "text/csv")
