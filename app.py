from contextlib import closing
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import sqlite3
import uuid

import pandas as pd
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

ROOT = Path(__file__).resolve().parent
today = datetime.now(ZoneInfo("Asia/Seoul")).date()
st.set_page_config(page_title="정윤하의 대여 장부", page_icon=str(ROOT / "logo.png"))
try:
    settings = st.secrets.to_dict()
except StreamlitSecretNotFoundError:
    settings = {}

def database():
    if settings.get("DATABASE_URL"):
        import psycopg
        return psycopg.connect(settings["DATABASE_URL"], connect_timeout=10)
    return sqlite3.connect(ROOT / "ledger.sqlite", timeout=10)

def records(entry=None):
    with closing(database()) as conn, conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS loans
            (id TEXT PRIMARY KEY, name TEXT NOT NULL, day TEXT NOT NULL,
             amount BIGINT NOT NULL CHECK(amount > 0))""")
        if entry:
            marker = "%s" if settings.get("DATABASE_URL") else "?"
            conn.execute("INSERT INTO loans VALUES (" + ", ".join([marker]*4)
                         + ") ON CONFLICT(id) DO NOTHING", entry)
        rows = conn.execute("SELECT name, day, amount FROM loans ORDER BY day, name").fetchall()
    return pd.DataFrame(rows, columns=["이름", "날짜", "금액"])

def go(page):
    st.session_state.page = page
    st.rerun()

def dashboard(df):
    name = st.session_state.viewer
    st.header(f"{name}님의 대여 현황")
    if df.empty:
        st.info("아직 등록된 대여 기록이 없습니다.")
        return
    my = df[df["이름"] == name]
    st.metric("내 총 채무", f"{my['금액'].sum():,}원")
    totals = df.groupby("이름")["금액"].sum().sort_index()
    st.subheader("사람별 총 채무")
    st.bar_chart(totals, y_label="금액 (원)", color="#237C72")
    st.subheader("기간별 누적 채무")
    scope = st.radio("조회 대상", ["전체", "나"], horizontal=True)
    period = st.selectbox("집계 단위", ["일별", "월별"])
    part = (df if scope == "전체" else my).copy()
    if part.empty:
        st.info("이 이름으로 등록된 기록이 없습니다.")
    else:
        part["기간"] = part["날짜"].str[:7 if period == "월별" else 10]
        trend = part.groupby("기간")["금액"].sum().cumsum().reset_index()
        st.vega_lite_chart(trend, {"mark":{"type":"line","point":True,"color":"#237C72"},
            "encoding":{"x":{"field":"기간","type":"ordinal","sort":"ascending"},
                        "y":{"field":"금액","type":"quantitative","title":"누적 금액 (원)"},
                        "tooltip":[{"field":"기간"},{"field":"금액","format":",d","type":"quantitative"}]}},
            use_container_width=True)
    days = df.groupby("이름")["날짜"].min().map(lambda d: (today - datetime.fromisoformat(d).date()).days)
    for col, title, series, unit in zip(st.columns(2), ["총 채무 TOP 3","채무 기간 TOP 3"],
                                        [totals, days], ["원","일"]):
        col.subheader(title)
        top = series.sort_values(ascending=False, kind="stable").head(3)
        for i, (person, value) in enumerate(top.items(), 1):
            col.text(f"{i}위  {person} · {value:,}{unit}")
            col.progress(value / max(1, top.max()))
    st.caption("채무 기간은 각 사람의 첫 대여일부터 오늘까지입니다. 동점은 이름순입니다.")

st.image(str(ROOT / "logo.png"), width=80)
st.title("정윤하의 대여 장부")
page = st.session_state.get("page", "home")
if page != "home" and st.button("← 처음으로"):
    st.session_state.clear()
    go("home")
if page == "home":
    st.write("어떤 역할로 들어갈까요?")
    a, b = st.columns(2)
    if a.button("사용자", use_container_width=True):
        go("user")
    if b.button("개발자", use_container_width=True):
        go("login")
elif page in ("user", "login"):
    admin = page == "login"
    st.header("개발자 로그인" if admin else "사용자 입장")
    with st.form("entry"):
        name = st.text_input("이름", max_chars=50).strip()
        password = st.text_input("패스워드", type="password") if admin else ""
        submit = st.form_submit_button("입장")
    if submit:
        if admin and "ADMIN_PASSWORD" not in settings:
            st.error("배포 설정의 Secrets에 ADMIN_PASSWORD를 등록해 주세요.")
        elif admin and (name != "박선우" or password != settings["ADMIN_PASSWORD"]):
            st.error("입력한 정보가 옳지 않습니다,")
        elif name:
            st.session_state.viewer = name
            go("manage" if admin else "dashboard")
        else:
            st.error("이름을 입력해 주세요.")
else:
    try:
        if page == "manage":
            st.header("대여 기록 등록")
            with st.form("loan", clear_on_submit=True):
                person = st.text_input("빌린 사람", max_chars=50).strip()
                day = st.date_input("빌려준 날짜", value=today, max_value=today)
                amount = st.number_input("빌려준 금액 (원)", min_value=1, max_value=100000000000, value=None, step=1)
                save = st.form_submit_button("등록")
            if save and person and amount:
                key = st.session_state.setdefault("transaction", str(uuid.uuid4()))
                records((key, person, day.isoformat(), amount))
                del st.session_state.transaction
                st.success(f"{person}의 대여금 {amount:,}원을 등록했습니다.")
            elif save:
                st.error("빌린 사람과 금액을 입력해 주세요.")
            st.subheader("등록된 대여 기록")
            st.dataframe(records().iloc[::-1], hide_index=True, use_container_width=True)
        else:
            dashboard(records())
    except (ConnectionError, sqlite3.Error):
        st.error("장부 연결에 실패했습니다. 데이터베이스 설정을 확인해 주세요.")
