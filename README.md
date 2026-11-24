# 정윤하의 대여 장부
ZIP을 풀고 app.py, logo.png, requirements.txt 등을 같은 GitHub 저장소의 최상위에 올립니다. Streamlit Community Cloud에서 해당 저장소와 브랜치를 선택하고 실행 파일에 app.py를 입력합니다.

Advanced settings → Secrets에 아래 설정을 입력합니다. ADMIN_PASSWORD 값에는 요청한 네 자리 비밀번호를 따옴표 안에 넣습니다. DATABASE_URL에는 쓰기 권한이 있는 PostgreSQL 연결 문자열을 넣습니다. 첫 실행 시 loans 테이블이 생성됩니다.

```toml
ADMIN_PASSWORD = "여기에 비밀번호 입력"
DATABASE_URL = "postgresql://USER:PASSWORD@HOST:5432/DB?sslmode=require"
```

로컬에서는 같은 설정을 .streamlit/secrets.toml에 넣고 pip install -r requirements.txt 후 streamlit run app.py로 실행합니다. DATABASE_URL을 생략하면 로컬 SQLite 파일을 사용합니다. 클라우드 재배포 후 기록을 유지하려면 외부 PostgreSQL을 연결하세요.

사용자는 이름만으로 입장하며 전체 사람별 금액과 순위를 볼 수 있습니다. 입력된 대여금은 계속 누적되며 기간은 첫 대여일부터 한국 시간 오늘까지의 경과 일수입니다.
