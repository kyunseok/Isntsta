import streamlit as st
import pandas as pd
import zipfile

# 분리한 모듈들을 불러옵니다.
from dataParser import InstagramHTMLParser
from analyzer import InstagramAnalyzer

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
        st.title("🕵️‍♂️ Isntsta")
        st.write("나를 맞팔하지 않는 사람 추적")
        
        self.render_upload_section()
        self.render_analysis_section()

    def render_upload_section(self):
        tab1, tab2 = st.tabs(["📦 ZIP 파일로 한 번에 업로드", "📄 HTML 파일 개별 업로드"])

        with tab1:
            st.info("💡 인스타그램에서 다운로드한 **.zip 파일**을 압축 해제하지 말고 그대로 올려주세요.")
            zip_file = st.file_uploader("ZIP 파일 업로드", type=['zip'], key='zip_upload', on_change=self.reset_analysis)
            
            if zip_file is not None and not st.session_state['data_loaded']:
                try:
                    with zipfile.ZipFile(zip_file) as z:
                        followers_path = next((f for f in z.namelist() if f.split('/')[-1].startswith('followers') and f.endswith('.html')), None)
                        following_path = next((f for f in z.namelist() if f.split('/')[-1].startswith('following') and f.endswith('.html')), None)
                                
                        if followers_path and following_path:
                            with st.spinner("데이터를 분석 중입니다..."):
                                st.session_state['followers_df'] = InstagramHTMLParser.parse(z.read(followers_path))
                                st.session_state['following_df'] = InstagramHTMLParser.parse(z.read(following_path))
                            st.session_state['data_loaded'] = True
                        else:
                            st.error("유효하지 않은 파일")
                except Exception as e:
                    st.error(f"오류가 발생했습니다.")

        with tab2:
            col1, col2 = st.columns(2)
            with col1:
                followers_upload = st.file_uploader("followers.html 업로드", type=['html'], key='followers_indiv', on_change=self.reset_analysis)
            with col2:
                following_upload = st.file_uploader("following.html 업로드", type=['html'], key='following_indiv', on_change=self.reset_analysis)
                
            if followers_upload and following_upload and not st.session_state['data_loaded']:
                with st.spinner("데이터를 분석 중입니다..."):
                    st.session_state['followers_df'] = InstagramHTMLParser.parse(followers_upload.getvalue())
                    st.session_state['following_df'] = InstagramHTMLParser.parse(following_upload.getvalue())
                st.session_state['data_loaded'] = True

    def render_analysis_section(self):
        st.divider()

        deactivated_input = st.text_area(
            "🚫 분석에서 제외할 계정 (비활성화, 브랜드, 대형 크리에이터 등) - 선택사항", 
            placeholder="쉼표(,) 또는 줄바꿈으로 구분하여 입력하세요.\n예: gov_korea, k_yseok.07"
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
        * 특정 계정이 비활성화, 정지, 삭제된 경우 실제 팔로워 / 팔로링 수와 다를 수 있습니다.
        * 아래 표는 참고용일 뿐이며, 실제 결과는 반드시 앱을 이용하여 확인하시기 바랍니다.
        """)
        
        st.divider()
        st.subheader("👀 Isntsta분석 결과")
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
