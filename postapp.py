import streamlit as st
import pandas as pd
import googlemaps
import pgeocode

# --- ページ設定 ---
st.set_page_config(page_title="電車距離計算アプリ", layout="wide")
st.title("🚃 郵便番号とGoogle Maps APIを使った電車移動距離計算")

# --- APIキー読み込み ---
st.header("① Google Maps APIキーのアップロード")
api_file = st.file_uploader("APIキー（.txt形式、1行目にキー）", type="txt")

if not api_file:
    st.warning("APIキーのアップロードをお待ちしています。")
    st.stop()

try:
    api_key = api_file.readline().decode("utf-8").strip()
    gmaps = googlemaps.Client(key=api_key)
    st.success("APIキーを読み込みました。")
except Exception as e:
    st.error(f"APIキーの読み込みに失敗しました：{e}")
    st.stop()

# --- 病院名の入力（最大10件） ---
st.header("② 病院名の入力（最大10件）")
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

# --- ファイルのアップロード ---
st.header("③ 郵便番号付きのCSVまたはExcelファイルをアップロード")
uploaded_file = st.file_uploader("ファイルを選択してください（CSVまたはExcel）", type=["csv", "xlsx"])

if not uploaded_file:
    st.info("ファイルのアップロードをお待ちしています。")
    st.stop()

# --- ファイル読み込み ---
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

# --- 郵便番号列の選択 ---
postal_col = st.selectbox("郵便番号の列を選んでください", df.columns)

# --- 郵便番号 → 簡易住所 ---
st.header("④ 郵便番号から住所変換")
nomi = pgeocode.Nominatim("jp")
addresses = []

for code in df[postal_col]:
    try:
        if pd.isna(code):
            addresses.append(None)
            continue
        code_str = str(code).replace("-", "").replace("−", "").strip()
        result = nomi.query_postal_code(code_str)
        if pd.isna(result.place_name) or pd.isna(result.prefecture_name):
            addresses.append(None)
        else:
            addr = f"{result.prefecture_name}{result.place_name}"
            addresses.append(addr)
    except:
        addresses.append(None)

df["住所"] = addresses

# --- 距離と時間を Google Maps で取得 ---
st.header("⑤ 公共交通機関での距離と所要時間を取得（Google Maps）")

for hosp in hospital_names:
    dist_list = []
    time_list = []

    for addr in df["住所"]:
        if addr is None:
            dist_list.append(None)
            time_list.append(None)
            continue

        try:
            directions = gmaps.directions(
                origin=addr,
                destination=hosp,
                mode="transit",  # 電車・バス等の公共交通
                language="ja",
                departure_time="now"
            )
            if not directions:
                raise ValueError("ルートが見つかりませんでした")

            leg = directions[0]['legs'][0]
            dist_km = round(leg['distance']['value'] / 1000, 2)
            time_min = round(leg['duration']['value'] / 60)

        except Exception:
            dist_km = None
            time_min = None

        dist_list.append(dist_km)
        time_list.append(time_min)

    df[f"{hosp}までの距離(km)"] = dist_list
    df[f"{hosp}までの時間(min)"] = time_list

# --- 結果表示・ダウンロード ---
st.header("⑥ 結果の確認とダウンロード")
st.dataframe(df)

csv = df.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 結果をCSVでダウンロード", csv, "電車距離結果.csv", "text/csv")
