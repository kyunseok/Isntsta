import streamlit as st
from bs4 import BeautifulSoup
import pandas as pd
import zipfile

class InstagramAppUI:
    """Streamlit UI 렌더링 및 애플리케이션 상태 관리를 담당합니다."""
    
    def __init__(self):
        self.setup_page()
        self.init_session_state()

    def setup_page(self):
        st.set_page_config(page_title="인스타그램 맞팔 분석기", page_icon="🕵️‍♂️", layout="centered")

    def init_session_state(self):
        if 'analyzed' not in st.session_state:
            st.session_state['analyzed'] = False
        if 'data_loaded' not in st.session_state:
            st.session_state['data_loaded'] = False

    def reset_analysis(self):
        st.session_state['analyzed'] = False
        st.session_state['data_loaded'] = False

    def run(self):
        st.title("🕵️‍♂️ 인스타그램 맞팔 분석기")
        st.write("인스타그램 백업 데이터를 통해 나를 맞팔하지 않는 사람을 찾고, 팔로우 시작 날짜도 함께 확인해 보세요.")
        
        self.render_upload_section()
        self.render_analysis_section()

    def render_upload_section(self):
        # 탭을 2개로 줄이고 개별 파일 업로드를 제거했습니다.
        tab1, tab2 = st.tabs(["📖 사용 방법 (필독)", "📦 ZIP 파일 업로드"])

        # --- 탭 1: 사용 방법 ---
        with tab1:
            st.subheader("💡 인스타그램 데이터 다운로드 및 사이트 이용 방법")
            
            st.markdown("#### 1단계: 내 데이터 다운로드 요청하기")
            st.markdown("""
            1. 인스타그램 모바일 앱 프로필에서 우측 상단 **메뉴(줄 3개)** ➔ **[내 활동]** ➔ **[내 정보 다운로드]**를 누릅니다.
            2. **[정보 다운로드 또는 전송]** ➔ **[일부 정보]**를 선택하고 **'팔로워 및 팔로잉'** 항목만 체크합니다.
            3. 기기로 다운로드하기를 누른 후, 파일 형식을 반드시 **HTML**로 선택하세요! (JSON은 불가)
            4. 날짜 범위는 **[전체 기간]**으로 설정하고 다운로드를 요청합니다.
            """)
            # 꿀팁: 캡처 이미지를 깃허브에 올리고 아래 주소 대신 "step1.png" 처럼 파일명을 적어주세요.
            st.image("https://dummyimage.com/800x300/f0f2f6/000000.png&text=Step+1:+Instagram+App+Screenshots", caption="1단계: 인스타그램 설정 화면 예시")

            st.markdown("#### 2단계: ZIP 파일 다운로드")
            st.markdown("* 10분~1시간 내에 가입된 이메일로 알림이 오면, 링크를 눌러 `.zip` 형태의 백업 파일을 다운로드합니다.")
            st.image("https://dummyimage.com/800x200/f0f2f6/000000.png&text=Step+2:+Email+Download+Screenshot", caption="2단계: 이메일 다운로드 화면 예시")

            st.markdown("#### 3단계: 분석기에 파일 업로드하기")
            st.markdown("* 옆의 **[📦 ZIP 파일 업로드]** 탭을 클릭하고, 다운받은 `.zip` 파일을 **압축을 풀지 말고 그대로** 회색 박스 안에 끌어다 놓습니다.")
            st.image("https://dummyimage.com/800x250/f0f2f6/000000.png&text=Step+3:+Upload+ZIP+File", caption="3단계: 화면에 파일 업로드하기")

            st.markdown("#### 4단계: 분석 시작!")
            st.markdown("* 파일이 정상적으로 올라가면 화면 아래에 **[🚀 맞팔 분석 시작]** 버튼이 나타납니다. 버튼을 눌러 결과를 확인하세요!")

        # --- 탭 2: ZIP 파일 업로드 ---
        with tab2:
            st.info("💡 다운로드한 **.zip 파일**을 압축 해제하지 말고 그대로 올려주세요.")
            zip_file = st.file_uploader("ZIP 파일 업로드 (.zip)", type=['zip'], key='zip_upload', on_change=self.reset_analysis)
            
            if zip_file is not None and not st.session_state['data_loaded']:
                try:
                    with zipfile.ZipFile(zip_file) as z:
                        followers_path = next((f for f in z.namelist() if f.split('/')[-1].startswith('followers') and f.endswith('.html')), None)
                        following_path = next((f for f in z.namelist() if f.split('/')[-1].startswith('following') and f.endswith('.html')), None)
                                
                        if followers_path and following_path:
                            with st.spinner("데이터를 추출 중입니다. 잠시만 기다려주세요..."):
                                st.session_state['followers_df'] = InstagramHTMLParser.parse(z.read(followers_path))
                                st.session_state['following_df'] = InstagramHTMLParser.parse(z.read(following_path))
                            st.session_state['data_loaded'] = True
                            st.success("데이터 추출 완료! 화면 아래로 스크롤하여 분석을 시작하세요.")
                        else:
                            st.error("ZIP 파일 내부에 팔로워/팔로잉 데이터가 없습니다. 안내된 1단계 방법에 따라 HTML 형식으로 제대로 다운로드했는지 확인해 주세요.")
                except Exception as e:
                    st.error(f"ZIP 파일을 읽는 중 오류가 발생했습니다: {e}")

    def render_analysis_section(self):
        st.divider()

        deactivated_input = st.text_area(
            "🚫 분석에서 제외할 계정 (비활성화, 유명인, 브랜드 등) - 선택사항", 
            placeholder="쉼표(,) 또는 줄바꿈으로 구분하여 입력하세요.\n예: stepblockkr, starbucks_korea"
        )

        if st.session_state['data_loaded']:
            if st.button("🚀 맞팔 분석 시작", use_container_width=True):
                deactivated_list = [x.strip() for x in deactivated_input.replace(',', '\n').split('\n') if x.strip()]
                
                analyzer = InstagramAnalyzer(
                    st.session_state['followers_df'],
                    st.session_state['following_df'],
                    deactivated_list
                )
                
                st.session_state['analysis_result'] = analyzer.analyze()
                st.session_state['analyzed'] = True

            if st.session_state['analyzed']:
                self.render_results(st.session_state['analysis_result'])

    def render_results(self, result: dict):
        st.subheader("📊 데이터 요약")
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("총 팔로워", f"{result['total_followers']}명")
        col_b.metric("데이터상 총 팔로잉", f"{result['total_following']}명")
        col_c.metric("나를 맞팔하지 않는 사람", f"{result['unfollowers_count']}명", delta="-언팔로워", delta_color="inverse")
        
        st.warning("""
        **⚠️ 분석 결과 확인 전 주의사항**
        * 앱에서 보이는 팔로잉 수와 위 '데이터상 총 팔로잉 수'가 다를 수 있습니다. (비활성화, 삭제, 정지된 계정이 데이터에는 포함되기 때문입니다)
        * 의심되는 계정은 표 안의 링크를 클릭해 직접 확인해 보세요!
        """)
        
        st.divider()
        st.subheader("👀 나를 맞팔하지 않는 계정 목록")
        st.caption("표 안의 파란색 **인스타그램 아이디**를 클릭하면 프로필로 이동합니다. **컬럼 제목(Date 등)을 클릭하여 오름차순/내림차순을 바꿀 수 있습니다.**")
        
        result_df = result['result_df']
        
        if not result_df.empty:
            result_df = result_df.sort_values(by="Parsed_Date", ascending=True, na_position='last').reset_index(drop=True)
            
            st.dataframe(
                result_df[["Profile_URL", "Date"]],
                column_config={
                    "Profile_URL": st.column_config.LinkColumn(
                        "사용자 이름 (클릭 시 이동)",
                        display_text="https://www\\.instagram\\.com/([^/]+)/?"
                    ),
                    "Date": st.column_config.Column(
                        "내가 팔로우를 시작한 날짜"
                    )
                },
                hide_index=True,
                use_container_width=True
            )
            
            with st.expander("📝 텍스트로 아이디만 복사하기"):
                st.code('\n'.join(result_df['Username'].tolist()))
        else:
            st.balloons()
            st.success("모든 팔로잉 사용자가 회원님을 맞팔하고 있습니다! 🎉")

# ==========================================
# 앱 실행
# ==========================================
if __name__ == "__main__":
    app = InstagramAppUI()
    app.run()
