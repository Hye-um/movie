
# 어제의 박스오피스 🎬
# 영화진흥위원회(KOBIS) 공식 API를 이용하는 스트림릿 앱

import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.express as px
import requests
import streamlit as st


# 1. 기본 화면 설정
st.set_page_config(
    page_title="어제의 박스오피스",
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


# 3. 제목과 설명
st.title("🎬 어제의 박스오피스")
st.write("영화진흥위원회(KOBIS) 공식 API로 어제의 영화 순위를 확인해 보세요.")


# 4. 한국 시간 기준으로 어제 날짜 계산
# 서버의 시간대가 한국 시간이 아니어도 정확하게 계산할 수 있어요.
KST = ZoneInfo("Asia/Seoul")
today_kst = datetime.datetime.now(KST).date()
yesterday = today_kst - datetime.timedelta(days=1)

# API에는 반드시 YYYYMMDD 형식으로 전달해요.
# 예: 20261025 (하이픈 없음)
target_date = yesterday.strftime("%Y%m%d")

# 화면에는 사람이 읽기 편한 형식으로 표시해요.
display_date = yesterday.strftime("%Y년 %m월 %d일")

st.subheader(f"📅 조회 날짜: {display_date}")
st.caption(f"API 조회 날짜: {target_date}")


# 5. API 주소 설정
API_URL = (
    "https://www.kobis.or.kr/kobisopenapi/"
    "webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
)


# 6. 인증키 확인
# 실제 인증키를 코드에 직접 적지 않고 Streamlit 비밀 금고에서 가져와요.
try:
    API_KEY = st.secrets["KOBIS_KEY"]
except (KeyError, FileNotFoundError):
    st.error(
        "🔑 인증키를 찾을 수 없습니다.\n\n"
        "Streamlit Cloud의 앱 설정에서 Secrets를 열고 "
        "아래 내용을 등록했는지 확인해 주세요."
    )
    st.code('KOBIS_KEY = "발급받은_본인_API_키"')
    st.info(
        "위 문구는 Secrets에 입력할 형식 예시입니다. "
        "실제 발급받은 키를 Secrets에 입력하고 앱을 다시 실행하세요."
    )
    st.stop()


# 7. API 요청
try:
    # URL에 날짜를 직접 이어 붙이지 않고 params로 전달해요.
    response = requests.get(
        API_URL,
        params={
            "key": API_KEY,
            "targetDt": target_date
        },
        timeout=20
    )

    # HTTP 요청 자체가 실패했다면 오류를 발생시켜요.
    response.raise_for_status()

    # 응답 내용을 JSON 형식으로 읽어요.
    data = response.json()

except requests.exceptions.Timeout:
    st.error("⏰ API 응답 시간이 초과되었습니다.")
    st.info(
        "인터넷 연결 상태와 KOBIS 서버 상태를 확인한 뒤 "
        "잠시 후 다시 실행해 주세요."
    )
    st.stop()

except requests.exceptions.HTTPError as e:
    st.error("🌐 API 서버에서 HTTP 오류가 발생했습니다.")
    st.write(f"오류 내용: {e}")
    st.info(
        "요청 주소, 인터넷 연결, KOBIS 서버 상태를 확인해 주세요."
    )
    st.stop()

except requests.exceptions.RequestException as e:
    st.error("🌐 API에 연결하지 못했습니다.")
    st.write(f"오류 내용: {e}")
    st.info(
        "인터넷 연결과 API 주소를 확인하고 다시 시도해 주세요."
    )
    st.stop()

except ValueError:
    st.error("📄 API 응답을 JSON으로 읽을 수 없습니다.")
    st.info(
        "KOBIS API가 정상적인 JSON을 반환하는지 확인해 주세요."
    )
    st.stop()


# 8. API 자체 오류 확인
# HTTP 상태 코드가 200이어도 API 내부 오류가 있을 수 있어요.
if not isinstance(data, dict):
    st.error("API 응답 형식이 올바르지 않습니다.")
    st.info("KOBIS API 응답 형식과 서버 상태를 확인해 주세요.")
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
        "인증키가 올바른지, API 사용 신청이 정상적으로 되었는지, "
        "요청 주소와 조회 날짜가 올바른지 확인해 주세요."
    )
    st.stop()


# 9. 박스오피스 결과 확인
boxoffice_result = data.get("boxOfficeResult")

if not isinstance(boxoffice_result, dict):
    st.error("박스오피스 결과를 찾을 수 없습니다.")
    st.info(
        "KOBIS API 응답 구조와 인증키, 요청 날짜를 확인해 주세요."
    )
    st.stop()

movie_list = boxoffice_result.get("dailyBoxOfficeList", [])

if not isinstance(movie_list, list) or len(movie_list) == 0:
    st.warning(f"{display_date}의 영화 목록이 비어 있습니다.")
    st.info(
        "해당 날짜의 집계 자료가 아직 제공되지 않았거나, "
        "API 응답에 영화 목록이 없는 상태일 수 있습니다. "
        "조회 날짜와 KOBIS 공식 사이트의 집계 현황을 확인해 주세요."
    )
    st.stop()


# 10. 데이터를 표와 그래프에 사용할 수 있도록 정리
df = pd.DataFrame(movie_list)

# API는 숫자처럼 보이는 값도 문자열로 보내므로 정수로 변환해요.
# 쉼표가 포함되어 있더라도 안전하게 처리합니다.
def to_number(value):
    """문자열로 받은 숫자를 정수로 바꾸는 함수"""
    try:
        cleaned = str(value).replace(",", "").strip()
        return int(cleaned)
    except (ValueError, TypeError):
        return 0


# 순위, 관객수, 누적관객수, 스크린 수를 숫자로 변환해요.
numeric_columns = {
    "rank": "순위",
    "audiCnt": "관객수",
    "audiAcc": "누적관객",
    "scrnCnt": "스크린수"
}

for column in numeric_columns:
    if column in df.columns:
        df[column] = df[column].apply(to_number)
    else:
        df[column] = 0

# 영화명과 개봉일이 없는 경우에도 앱이 멈추지 않도록 해요.
for column in ["movieNm", "openDt"]:
    if column not in df.columns:
        df[column] = "정보 없음"

# 순위가 숫자 기준으로 정렬되도록 해요.
df = df.sort_values("rank").reset_index(drop=True)


# 11. 1위 영화 정보 표시
first_movie = df.iloc[0]

st.divider()
st.header("🏆 어제의 1위 영화")
st.subheader(str(first_movie["movieNm"]))

# 세 장의 지표 카드를 나란히 표시해요.
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


# 12. 관객수 상위 5편 막대그래프
st.divider()
st.header("📊 관객수 상위 5편")

top5 = (
    df.sort_values("audiCnt", ascending=False)
    .head(5)
    .sort_values("audiCnt", ascending=True)
    .copy()
)

# 그래프에 순위와 영화명을 함께 표시해요.
top5["영화"] = (
    top5["rank"].astype(str)
    + "위 · "
    + top5["movieNm"].astype(str)
)

fig = px.bar(
    top5,
    x="audiCnt",
    y="영화",
    orientation="h",
    text="audiCnt",
    labels={
        "audiCnt": "당일 관객수(명)",
        "영화": "영화"
    },
    color="audiCnt",
    color_continuous_scale=["#F8D98B", "#D97706"]
)

# 막대 끝에 관객수를 천 단위 쉼표와 함께 표시해요.
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
    yaxis=dict(
        title=""
    ),
    margin=dict(l=10, r=90, t=20, b=20)
)

st.plotly_chart(fig, use_container_width=True)


# 13. 전체 영화 순위 표
st.divider()
st.header("🎞️ 전체 박스오피스 순위")

# 표에 필요한 열만 골라서 한국어 이름으로 바꿔요.
table_df = df[
    ["rank", "movieNm", "openDt", "audiCnt", "audiAcc", "scrnCnt"]
].copy()

table_df.columns = [
    "순위",
    "영화명",
    "개봉일",
    "관객수",
    "누적관객",
    "스크린수"
]

# 표에서도 관객수 등이 문자열이 아니라 숫자 자료형으로 유지돼요.
st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "순위": st.column_config.NumberColumn(
            "순위",
            format="%d위"
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

st.caption(
    f"자료 출처: 영화진흥위원회(KOBIS) 일별 박스오피스 API · "
    f"조회일 {target_date}"
)
