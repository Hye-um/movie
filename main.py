
# 어제의 박스오피스 🎬
# 날짜를 직접 선택하고 영화 순위, 관객수, 순위 변동을 확인하는 앱

import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import requests
import streamlit as st


# 1. 기본 화면 설정
st.set_page_config(
    page_title="박스오피스 탐험",
    page_icon="🎬",
    layout="wide"
)


# 2. 화면 디자인
st.markdown("""
<style>
    .stApp {
        background-color: #FFF9ED;
    }

    h1, h2, h3 {
        color: #754C24;
    }

    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #F0D9A7;
        padding: 20px;
        border-radius: 15px;
    }
</style>
""", unsafe_allow_html=True)


# 3. 제목
st.title("🎬 박스오피스 탐험")
st.write("날짜를 선택하고 그날의 영화 순위와 관객수를 확인해 보세요!")


# 4. 한국 시간 기준으로 오늘과 어제 계산
# 서버의 시간대가 한국 시간이 아니어도 정확하게 계산돼요.
KST = ZoneInfo("Asia/Seoul")
today_kst = datetime.datetime.now(KST).date()
yesterday = today_kst - datetime.timedelta(days=1)


# 5. 날짜 선택 달력
st.subheader("📅 박스오피스 조회 날짜")

selected_date = st.date_input(
    "조회할 날짜를 선택하세요.",
    value=yesterday,
    min_value=datetime.date(2004, 11, 11),
    max_value=yesterday,
    format="YYYY-MM-DD"
)

# API에는 하이픈이 없는 8자리 날짜를 전달해요.
# 예: 20261025
target_date = selected_date.strftime("%Y%m%d")

st.caption(
    f"선택한 날짜: {selected_date.strftime('%Y년 %m월 %d일')} "
    f"({target_date})"
)


# 6. API 주소
API_URL = (
    "https://www.kobis.or.kr/kobisopenapi/"
    "webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
)


# 7. 인증키 가져오기
# 실제 인증키는 코드에 쓰지 않고 Streamlit Secrets에서 읽어요.
try:
    API_KEY = st.secrets["KOBIS_KEY"]

except (KeyError, FileNotFoundError):
    st.error("🔑 KOBIS API 인증키를 찾을 수 없습니다.")
    st.info(
        "Streamlit Cloud의 앱 설정 → Secrets에서 "
        "KOBIS_KEY를 등록했는지 확인해 주세요."
    )
    st.code('KOBIS_KEY = "본인의_API_인증키"')
    st.stop()


# 8. 선택한 날짜의 API 자료 가져오기
try:
    response = requests.get(
        API_URL,
        params={
            "key": API_KEY,
            "targetDt": target_date
        },
        timeout=20
    )

    response.raise_for_status()
    data = response.json()

except requests.exceptions.Timeout:
    st.error("⏰ API 응답 시간이 초과되었습니다.")
    st.info(
        "인터넷 연결이나 KOBIS 서버 상태를 확인한 후 "
        "잠시 뒤 다시 실행해 주세요."
    )
    st.stop()

except requests.exceptions.HTTPError as e:
    st.error("🌐 API 서버에서 HTTP 오류가 발생했습니다.")
    st.write(f"오류 내용: {e}")
    st.info("API 주소와 서버 상태를 확인해 주세요.")
    st.stop()

except requests.exceptions.RequestException as e:
    st.error("🌐 API에 연결할 수 없습니다.")
    st.write(f"오류 내용: {e}")
    st.info("인터넷 연결과 API 주소를 확인해 주세요.")
    st.stop()

except ValueError:
    st.error("📄 API 응답을 JSON으로 읽을 수 없습니다.")
    st.info("KOBIS API 응답이 정상인지 확인해 주세요.")
    st.stop()


# 9. API에서 반환한 오류 확인
if not isinstance(data, dict):
    st.error("API 응답 형식이 올바르지 않습니다.")
    st.info("KOBIS API의 응답 형식을 확인해 주세요.")
    st.stop()

if "faultInfo" in data:
    fault = data["faultInfo"]

    st.error("🚨 KOBIS API에서 오류를 반환했습니다.")

    if isinstance(fault, dict):
        st.write(
            f"오류 코드: {fault.get('errorCode', '확인 불가')}"
        )
        st.write(
            f"오류 내용: {fault.get('message', '확인 불가')}"
        )
    else:
        st.write(f"오류 내용: {fault}")

    st.info(
        "인증키, API 사용 권한, 요청 주소와 선택 날짜를 확인해 주세요."
    )
    st.stop()


# 10. 박스오피스 결과 확인
boxoffice_result = data.get("boxOfficeResult")

if not isinstance(boxoffice_result, dict):
    st.error("박스오피스 결과를 찾을 수 없습니다.")
    st.info("API 응답과 조회 날짜를 확인해 주세요.")
    st.stop()

movie_list = boxoffice_result.get("dailyBoxOfficeList", [])

# 영화 목록이 비어 있으면 집계 전 안내를 표시해요.
if not isinstance(movie_list, list) or len(movie_list) == 0:
    st.warning("📢 그날은 아직 집계 전입니다")
    st.info(
        "선택한 날짜의 박스오피스 자료가 아직 제공되지 않았거나 "
        "해당 날짜의 영화 목록이 비어 있습니다. "
        "다른 날짜를 선택하거나 KOBIS 공식 사이트에서 "
        "집계 현황을 확인해 주세요."
    )
    st.stop()


# 11. 문자열 숫자를 정수로 바꾸는 함수
def to_number(value):
    """API에서 문자열로 온 숫자를 정수로 바꿔요."""
    try:
        return int(str(value).replace(",", "").strip())
    except (ValueError, TypeError):
        return 0


# 12. 데이터를 표와 그래프에 사용할 수 있도록 정리
df = pd.DataFrame(movie_list)

# 순위, 관객수, 누적관객, 스크린 수, 순위 증감을 숫자로 변환해요.
numeric_columns = [
    "rank",
    "rankInten",
    "audiCnt",
    "audiAcc",
    "scrnCnt"
]

for column in numeric_columns:
    if column in df.columns:
        df[column] = df[column].apply(to_number)
    else:
        df[column] = 0

# 영화명과 개봉일이 누락된 경우에도 앱이 멈추지 않도록 해요.
for column in ["movieNm", "openDt"]:
    if column not in df.columns:
        df[column] = "정보 없음"

df = df.sort_values("rank").reset_index(drop=True)


# 13. 영화명 옆에 트로피 붙이기
# 누적관객이 100만 명을 초과한 영화만 표시해요.
def add_trophy(row):
    movie_name = str(row["movieNm"])

    if int(row["audiAcc"]) > 1_000_000:
        return f"🏆 {movie_name}"

    return movie_name


df["표시 영화명"] = df.apply(add_trophy, axis=1)


# 14. 순위 변동 화살표 만들기
# 사용자가 알려 준 기준에 따라 양수는 상승, 음수는 하락이에요.
def rank_change_text(value):
    change = int(value)

    if change > 0:
        return f"🔴 ⬆️ +{change}"
    elif change < 0:
        return f"🔵 ⬇️ {change}"
    else:
        return "➖ 0"


# 15. 1위 영화 지표 카드 3개
first_movie = df.iloc[0]

st.divider()
st.header("🏆 선택한 날짜의 1위 영화")
st.subheader(str(first_movie["표시 영화명"]))

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="🎟️ 당일 관객수",
        value=f"{int(first_movie['audiCnt']):,}명"
    )

with col2:
    st.metric(
        label="👥 누적 관객수",
        value=f"{int(first_movie['audiAcc']):,}명"
    )

with col3:
    st.metric(
        label="🖥️ 스크린 수",
        value=f"{int(first_movie['scrnCnt']):,}개"
    )


# 16. 관객수 상위 5편 막대그래프
st.divider()
st.header("📊 관객수 상위 5편")

top5 = (
    df.sort_values("audiCnt", ascending=False)
    .head(5)
    .sort_values("audiCnt", ascending=True)
    .copy()
)

top5["영화"] = (
    top5["rank"].astype(str)
    + "위 · "
    + top5["표시 영화명"].astype(str)
)

fig = px.bar(
    top5,
    x="audiCnt",
    y="영화",
    orientation="h",
    text="audiCnt",
    labels={
        "audiCnt": "당일 관객수(명)",
        "영화": "영화명"
    },
    color="audiCnt",
    color_continuous_scale=["#F8D98B", "#D97706"]
)

fig.update_traces(
    texttemplate="%{text:,}명",
    textposition="outside",
    cliponaxis=False
)

fig.update_layout(
    plot_bgcolor="#FFF9ED",
    paper_bgcolor="#FFF9ED",
    font=dict(family="sans-serif", size=14),
    coloraxis_showscale=False,
    xaxis=dict(
        rangemode="tozero",
        tickformat=","
    ),
    yaxis=dict(title=""),
    margin=dict(l=10, r=90, t=20, b=20)
)

st.plotly_chart(fig, use_container_width=True)


# 17. 전체 영화 순위 표
st.divider()
st.header("🎞️ 전체 박스오피스 순위")

# 표에 표시할 데이터를 새로 만들어요.
table_df = pd.DataFrame({
    "순위": df["rank"],
    "순위 증감": df["rankInten"].apply(rank_change_text),
    "영화명": df["표시 영화명"],
    "개봉일": df["openDt"],
    "관객수": df["audiCnt"],
    "누적관객": df["audiAcc"],
    "스크린수": df["scrnCnt"]
})

st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "순위": st.column_config.NumberColumn(
            "순위",
            format="%d위"
        ),
        "순위 증감": st.column_config.TextColumn(
            "전일 대비 순위 변동"
        ),
        "관객수": st.column_config.NumberColumn(
            "관객수",
            format="%d명"
        ),
        "누적관객": st.column_config.NumberColumn(
            "누적관객",
            format="%d명"
        ),
        "스크린수": st.column_config.NumberColumn(
            "스크린수",
            format="%d개"
        )
    }
)

# 18. 화살표와 트로피 설명
st.caption("🔴 ⬆️ 순위 상승  |  🔵 ⬇️ 순위 하락  |  ➖ 순위 변동 없음")
st.caption("🏆 누적 관객수가 100만 명을 초과한 영화")
st.caption(
    f"자료 출처: 영화진흥위원회(KOBIS) 일별 박스오피스 API · "
    f"조회일 {target_date}"
)
