import streamlit as st
import pandas as pd
import zipfile

from dataParser import InstagramDataParser
from analyzer import InstagramAnalyzer

class InstagramAppUI:
    """Streamlit UI 렌더링 및 애플리케이션 상태 관리를 담당합니다."""
    
    def __init__(self):
        self.setup_page()
        self.init_session_state()

    def setup_page(self):
        st.set_page_config(page_title="Isntsta", page_icon="🕵️‍♂️", layout="centered")

    def init_session_state(self):
        if 'analyzed' not in st.session_state:
            st.session_state['analyzed'] = False
        if 'data_loaded' not in st.session_state:
            st.session_state['data_loaded'] = False

    def reset_analysis(self):
        st.session_state['analyzed'] = False
        st.session_state['data_loaded'] = False

    def run(self):
        st.title("🕵️‍♂️ Isntsta")
        st.write("나를 맞팔하지 않는 사람을 찾아보세요.")
        
        tab1, tab2 = st.tabs(["📖 사용 방법", "📦 ZIP 파일 업로드"])

        with tab1:
            self.render_instructions()

        with tab2:
            self.render_upload_section()
            self.render_analysis_section()

    def render_instructions(self):
        st.subheader("💡 인스타그램 데이터 다운로드 및 사이트 이용 방법")
        
        st.markdown("#### 1단계: Instagram에 내 데이터 다운로드 요청하기")
        st.markdown("""
        1. Instagram 앱에서 **메뉴(줄 3개)** ➔ **[계정 센터]** ➔ **[내 정보 및 권한]**을 누릅니다.
        2. **[내 정보 내보내기]** ➔ **[내보내기 만들기]** -> **Instagram** -> **[기기로 내보내기]**를 순서대로 선택합니다.

        - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        **[정보 맞춤 설정]**에 반드시 내 **'폴라워 및 팔로링' 정보가 있어야 합니다.
        또한 **[기간]**을 **'전체 기간'**으로 선택해야 정확한 분석이 가능합니다.
        - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        
        3. **[내보내기 시작]**을 누릅니다.
        """)
        st.image("instagramFileDownload.jpeg", caption="1단계: 인스타그램 설정 화면 예시")

        st.markdown("#### 2단계: ZIP 파일 다운로드")
        st.markdown("* 10분~1시간 내에 이메일로 알림이 오면, 링크를 눌러 `.zip` 파일을 다운로드합니다.")
        st.image("instagramGmail.png", caption="2단계: 이메일 다운로드 화면 예시")

        st.markdown("#### 3단계: 분석기에 파일 업로드하기")
        st.markdown("* 위 **[📦 ZIP 파일 업로드]** 탭을 클릭하고, 다운받은 `.zip` 파일을 **압축을 풀지 말고 그대로** 회색 박스 안에 끌어다 놓습니다.")
        st.image("https://dummyimage.com/800x250/f0f2f6/000000.png&text=Step+3:+Upload+ZIP+File", caption="3단계: 화면에 파일 업로드하기")

        st.markdown("#### 4단계: 분석 시작!")
        st.markdown("* 파일이 정상적으로 올라가면 나타나는 **[🚀 맞팔 분석 시작]** 버튼을 눌러 결과를 확인하세요!")

    def render_upload_section(self):
        st.info("💡 다운로드한 **.zip 파일**을 압축 해제하지 말고 그대로 올려주세요. (HTML, JSON 형식 모두 지원)")
        zip_file = st.file_uploader("ZIP 파일 업로드 (.zip)", type=['zip'], key='zip_upload', on_change=self.reset_analysis)
        
        if zip_file is not None and not st.session_state['data_loaded']:
            try:
                with zipfile.ZipFile(zip_file) as z:
                    # 확장자가 html 또는 json인 파일을 검색합니다.
                    followers_path = next((f for f in z.namelist() if f.split('/')[-1].startswith('followers') and f.endswith(('.html', '.json'))), None)
                    following_path = next((f for f in z.namelist() if f.split('/')[-1].startswith('following') and f.endswith(('.html', '.json'))), None)
                            
                    if followers_path and following_path:
                        followers_ext = followers_path.split('.')[-1]
                        following_ext = following_path.split('.')[-1]
                        
                        with st.spinner("데이터를 추출 중입니다. 잠시만 기다려주세요..."):
                            st.session_state['followers_df'] = InstagramDataParser.parse(z.read(followers_path), followers_ext)
                            st.session_state['following_df'] = InstagramDataParser.parse(z.read(following_path), following_ext)
                        st.session_state['data_loaded'] = True
                        st.success("데이터 추출 완료! 아래에서 분석을 시작하세요.")
                    else:
                        st.error("ZIP 파일 내부에 팔로워/팔로잉 데이터가 없습니다.")
            except Exception as e:
                st.error(f"ZIP 파일을 읽는 중 오류가 발생했습니다: {e}")

    def render_analysis_section(self):
        if st.session_state['data_loaded']:
            st.divider()

            deactivated_input = st.text_area(
                "🚫 분석에서 제외할 계정 (비활성화, 유명인, 브랜드 등) - 선택사항", 
                placeholder="쉼표(,) 또는 줄바꿈으로 구분하여 입력하세요.\n예: gov_korea, k_yseok.07"
            )

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
        * 비활성화, 삭제, 정지된 계정이 있을 경우 분석 결과가 실제와 다를 수 있습니다.
        * 분석 결과는 참고용일 뿐이며, 실제 결과는 반드시 Instagram 앱에 직접 들어가서 확인하시기 바랍니다.
        """)
        
        st.divider()
        st.subheader("👀 나를 맞팔하지 않는 계정 목록")
        st.caption("**인스타그램 아이디**를 클릭하면 프로필로 이동합니다.")
        
        result_df = result['result_df']
        
        if not result_df.empty:
            result_df = result_df.sort_values(by="Parsed_Date", ascending=True, na_position='last').reset_index(drop=True)
            
            st.dataframe(
                result_df[["Profile_URL", "Date"]],
                column_config={
                    "Profile_URL": st.column_config.LinkColumn(
                        "사용자 이름",
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

if __name__ == "__main__":
    app = InstagramAppUI()
    app.run()
