import streamlit as st
from bs4 import BeautifulSoup
import pandas as pd
import zipfile

class InstagramHTMLParser:
    """HTML 데이터를 파싱하여 데이터프레임으로 변환하는 책임을 가집니다."""
    
    @staticmethod
    @st.cache_data
    def parse(html_content: bytes) -> pd.DataFrame:
        soup = BeautifulSoup(html_content, 'html.parser')
        records = []
        
        for a_tag in soup.find_all('a'):
            href = a_tag.get('href', '')
            if 'instagram.com' in href:
                username = href.split('?')[0].strip('/').split('/')[-1]
                
                parent_div = a_tag.parent.parent
                date_str = ""
                parsed_date = pd.NaT 
                
                if parent_div:
                    divs = parent_div.find_all('div')
                    if len(divs) > 1:
                        raw_date = divs[-1].text.strip()
                        
                        try:
                            parts = raw_date.replace(',', '').split()
                            if len(parts) >= 5:
                                month = int(parts[0].replace('월', ''))
                                day = int(parts[1])
                                year = int(parts[2])
                                hour, minute = map(int, parts[3].split(':'))
                                ampm = parts[4]
                                
                                date_str = f"{year}년 {month}월 {day}일 {ampm} {hour}시 {minute}분"
                                
                                calc_hour = hour
                                if ampm == '오후' and hour != 12:
                                    calc_hour += 12
                                elif ampm == '오전' and hour == 12:
                                    calc_hour = 0
                                    
                                parsed_date = pd.Timestamp(year, month, day, calc_hour, minute)
                            else:
                                date_str = raw_date
                        except Exception:
                            date_str = raw_date
                        
                records.append({'Username': username, 'Date': date_str, 'Parsed_Date': parsed_date})
                
        return pd.DataFrame(records).drop_duplicates(subset=['Username'])

class InstagramAnalyzer:
    """팔로워/팔로잉 데이터를 비교하고 분석하는 비즈니스 로직을 담당합니다."""
    
    def __init__(self, followers_df: pd.DataFrame, following_df: pd.DataFrame, deactivated_list: list):
        self.followers_df = followers_df
        self.following_df = following_df
        self.deactivated_set = set(deactivated_list)

    def analyze(self) -> dict:
        followers_set = set(self.followers_df['Username'])
        following_set = set(self.following_df['Username'])
        
        filtered_following = following_set - self.deactivated_set
        filtered_followers = followers_set - self.deactivated_set
        
        unfollowers = filtered_following - filtered_followers
        
        result_df = self.following_df[self.following_df['Username'].isin(unfollowers)].copy()
        result_df["Profile_URL"] = result_df["Username"].apply(lambda x: f"https://www.instagram.com/{x}/")
        
        return {
            'total_followers': len(filtered_followers),
            'total_following': len(filtered_following),
            'unfollowers_count': len(unfollowers),
            'result_df': result_df
        }

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
                            st.error("ZIP 파일 내부에 팔로워/팔로잉 HTML 파일이 없습니다. 올바른 백업 파일인지 확인해주세요.")
                except Exception as e:
                    st.error(f"오류 발생: {e}")

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
            "🚫 분석에서 제외할 계정 (비활성화, 브랜드 등) - 선택사항", 
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
        st.caption("표 안의 파란색 **인스타그램 아이디**를 클릭하면 프로필로 이동합니다. **컬럼 제목을 클릭하여 정렬 방식을 바꿀 수 있습니다.**")
        
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

if __name__ == "__main__":
    app = InstagramAppUI()
    app.run()
