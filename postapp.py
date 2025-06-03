import streamlit as st
import pandas as pd
import googlemaps

# ------------------------------
# ページ設定
# ------------------------------
st.set_page_config(page_title="電車移動距離計算アプリ", layout="wide")
st.title("🚃 郵便番号とGoogle Maps APIによる電車距離・時間計算")

# ------------------------------
# ① APIキーのアップロード
# ------------------------------
st.header("① Google Maps APIキーのアップロード")
api_file = st.file_uploader("APIキー（1行目にAPIキーが書かれた .txt ファイル）", type="txt")

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

# ------------------------------
# ② 病院名の入力（最大10件、初期値あり）
# ------------------------------
st.header("② 病院名を入力してください（最大10件）")

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

# ------------------------------
# ③ ファイルのアップロード
# ------------------------------
st.header("③ 郵便番号が含まれるCSVまたはExcelファイルをアップロード")
uploaded_file = st.file_uploader("CSVまたはExcelファイルを選択してください", type=["csv", "xlsx"])

if not uploaded_file:
    st.stop()

# ------------------------------
# ④ ファイル読み込み
# ------------------------------
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

# ------------------------------
# ⑤ 郵便番号列の選択と正規化
# ------------------------------
postal_col = st.selectbox("郵便番号の列を選んでください", df.columns)

st.header("④ 郵便番号を住所形式に変換")
addresses = []
for code in df[postal_col]:
    try:
        if pd.isna(code):
            addresses.append(None)
            continue
        code_str = str(code).replace("-", "").replace("−", "").strip()
        if len(code_str) == 7 and code_str.isdigit():
            address = f"〒{code_str}"
        else:
            address = None
        addresses.append(address)
    except:
        addresses.append(None)

df["住所"] = addresses
st.write("変換された住所（先頭5件）:")
st.write(df["住所"].head())

# ------------------------------
# ⑥ Google Maps APIで電車ルート検索
# ------------------------------
st.header("⑤ 公共交通機関による距離・時間を計算（Google Maps）")

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
                raise ValueError("ルートが見つかりませんでした")

            leg = directions[0]["legs"][0]
            dist_km = round(leg["distance"]["value"] / 1000, 2)
            time_min = round(leg["duration"]["value"] / 60)

        except Exception as e:
            dist_km = None
            time_min = None

        dist_list.append(dist_km)
        time_list.append(time_min)

    df[f"{hosp}までの距離(km)"] = dist_list
    df[f"{hosp}までの時間(min)"] = time_list

# ------------------------------
# ⑦ 結果表示とダウンロード
# ------------------------------
st.header("⑥ 計算結果")
st.dataframe(df)

csv = df.to_csv(index=False).encode("utf-8-sig")
st.download_button("📥 結果をCSVでダウンロード", csv, "電車距離計算結果.csv", "text/csv")
