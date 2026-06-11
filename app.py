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
        st.write("나를 맞팔하지 않는 계정을 안전하고 빠르게 찾아보세요.")
        
        # 3개의 탭 구성 (사용 방법, 파일 업로드, 개발자 소개)
        tab1, tab2, tab3 = st.tabs(["📖 사용 방법", "📦 ZIP 파일 업로드", "🧑‍💻 개발자 소개"])

        with tab1:
            self.render_instructions()

        with tab2:
            self.render_upload_section()
            self.render_analysis_section()
            
        with tab3:
            self.render_about_section()

    def render_instructions(self):
        st.subheader("💡 인스타그램 데이터 다운로드 및 이용 방법")
        
        st.markdown("#### 1단계: Instagram에 내 데이터 다운로드 요청하기")
        st.markdown("""
        1. Instagram 앱에서 **메뉴(줄 3개)** ➔ **계정 센터** ➔ **내 정보 및 권한**으로 이동합니다.
        2. **내 정보 내보내기** ➔ **내보내기 만들기** ➔ **Instagram** ➔ **기기로 내보내기**를 순서대로 선택합니다.

        ---
        **중요 설정 안내**
        * **정보 맞춤 설정** 단계에서 반드시 **팔로워 및 팔로잉** 정보가 체크되어 있어야 합니다.
        * **기간** 설정 시 **전체 기간**을 선택하셔야 누락 없는 정확한 분석이 가능합니다.
        ---
        
        3. **내보내기 시작**을 누릅니다.
        """)
        # 통일된 규칙의 명확한 이미지 파일 이름으로 수정
        st.image("instagramFileDownload.jpg", caption="1단계: 인스타그램 데이터 요청 화면")

        st.markdown("#### 2단계: 백업 파일 다운로드")
        st.markdown("* 요청 후 대략 10분에서 1시간 이내에 인스타그램으로부터 이메일 알림이 도착합니다. 이메일 본문의 링크를 클릭하여 .zip 파일을 다운로드해 주세요.")
        st.image("instagramGmail.png", caption="2단계: 이메일 알림 및 다운로드 화면")

        st.markdown("#### 3단계: 분석기에 파일 업로드하기")
        st.markdown("* 상단의 **ZIP 파일 업로드** 탭을 선택한 뒤, 다운로드한 .zip 파일을 **압축을 풀지 말고 파일 업로드 박스에 그대로** 끌어다 놓습니다.")
        st.image("guide_file_upload.png", caption="3단계: 분석기 파일 업로드 화면")

        st.markdown("#### 4단계: 맞팔 분석 시작")
        st.markdown("* 파일이 정상적으로 올라가면 하단에 생성되는 **맞팔 분석 시작** 버튼을 클릭하여 결과를 확인합니다.")

    def render_upload_section(self):
        st.info("💡 다운로드한 .zip 파일을 압축 해제하지 말고 그대로 업로드해 주세요. (HTML 및 JSON 형식 모두 지원)")
        zip_file = st.file_uploader("ZIP 파일 업로드 (.zip)", type=['zip'], key='zip_upload', on_change=self.reset_analysis)
        
        if zip_file is not None and not st.session_state['data_loaded']:
            try:
                with zipfile.ZipFile(zip_file) as z:
                    followers_path = next((f for f in z.namelist() if f.split('/')[-1].startswith('followers') and f.endswith(('.html', '.json'))), None)
                    following_path = next((f for f in z.namelist() if f.split('/')[-1].startswith('following') and f.endswith(('.html', '.json'))), None)
                            
                    if followers_path and following_path:
                        followers_ext = followers_path.split('.')[-1]
                        following_ext = following_path.split('.')[-1]
                        
                        with st.spinner("데이터를 추출하고 있습니다. 잠시만 기다려 주세요..."):
                            st.session_state['followers_df'] = InstagramDataParser.parse(z.read(followers_path), followers_ext)
                            st.session_state['following_df'] = InstagramDataParser.parse(z.read(following_path), following_ext)
                        st.session_state['data_loaded'] = True
                        st.success("데이터 추출이 완료되었습니다. 아래에서 분석을 진행해 주세요.")
                    else:
                        st.error("ZIP 파일 내부에 팔로워 또는 팔로잉 데이터 파일이 존재하지 않습니다. 올바른 백업 파일인지 확인해 주세요.")
            except Exception as e:
                st.error(f"ZIP 파일을 읽는 중 오류가 발생했습니다: {e}")

    def render_analysis_section(self):
        if st.session_state['data_loaded']:
            st.divider()

            deactivated_input = st.text_area(
                "🚫 분석에서 제외할 계정 (비활성화 계정, 유명인, 브랜드 등) - 선택사항", 
                placeholder="쉼표 또는 줄바꿈으로 구분하여 입력해 주세요.\n예: gov_korea, k_yseok.07"
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
        * 상대방이 계정을 일시 비활성화, 삭제 또는 정지한 경우 실제 인스타그램 앱에 표시되는 수치와 다를 수 있습니다.
        * 본 분석 결과는 추출된 백업 데이터를 기반으로 하므로 참고용으로 활용하시고, 정확한 내역은 인스타그램 앱에서 직접 교차 확인하시는 것을 권장합니다.
        """)
        
        st.divider()
        st.subheader("👀 나를 맞팔하지 않는 계정 목록")
        st.caption("사용자 이름을 클릭하면 해당 사용자의 인스타그램 프로필 페이지로 바로 이동합니다. 열 제목을 클릭하여 정렬 순서를 바꿀 수 있습니다.")
        
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

    def render_about_section(self):
        st.subheader("Developer")
        
        st.markdown("""
        **윤슥**

        website:
        - Isntsta
        - KAnalyzer
        """)
        
        st.divider()
        st.info("본 분석기는 사용자의 인스타그램 백업 데이터를 외부 서버로 전송하거나 저장하지 않으며, 웹 브라우저의 로컬 메모리 내에서만 안전하게 동작합니다.")

if __name__ == "__main__":
    app = InstagramAppUI()
    app.run()
