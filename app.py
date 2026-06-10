import streamlit as st
from bs4 import BeautifulSoup
import pandas as pd
import zipfile

# 데이터를 캐싱하여 분석 속도를 높입니다.
@st.cache_data
def parse_instagram_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    records = []
    
    for a_tag in soup.find_all('a'):
        href = a_tag.get('href', '')
        if 'instagram.com' in href:
            # URL 파라미터가 붙어있을 경우를 대비해 순수 아이디만 안전하게 추출
            username = href.split('?')[0].strip('/').split('/')[-1]
            records.append({'Username': username})
            
    return pd.DataFrame(records).drop_duplicates()

st.set_page_config(page_title="인스타그램 맞팔 분석기", page_icon="🕵️‍♂️", layout="centered")

st.title("🕵️‍♂️ 인스타그램 맞팔 분석기")
st.write("인스타그램 백업 데이터를 통해 나를 맞팔하지 않는 사람을 찾고, 클릭 한 번으로 프로필을 확인해 보세요.")

tab1, tab2 = st.tabs(["📦 ZIP 파일로 한 번에 업로드", "📄 HTML 파일 개별 업로드"])

followers_df = None
following_df = None
data_loaded = False

# --- 탭 1: ZIP 파일 업로드 ---
with tab1:
    st.info("💡 인스타그램에서 다운로드한 **.zip 파일**을 압축 해제하지 말고 그대로 올려주세요.")
    zip_file = st.file_uploader("ZIP 파일 업로드", type=['zip'], key='zip_upload')
    
    if zip_file is not None:
        try:
            with zipfile.ZipFile(zip_file) as z:
                # 내부 파일 경로를 동적으로 탐색
                followers_path = next((f for f in z.namelist() if f.split('/')[-1].startswith('followers') and f.endswith('.html')), None)
                following_path = next((f for f in z.namelist() if f.split('/')[-1].startswith('following') and f.endswith('.html')), None)
                        
                if followers_path and following_path:
                    with st.spinner("데이터를 분석 중입니다..."):
                        followers_df = parse_instagram_html(z.read(followers_path))
                        following_df = parse_instagram_html(z.read(following_path))
                    data_loaded = True
                    st.success("데이터 추출 완료!")
                else:
                    st.error("ZIP 파일 내부에 팔로워/팔로잉 HTML 파일이 없습니다. 올바른 인스타그램 백업 파일인지 확인해주세요.")
        except Exception as e:
            st.error(f"오류 발생: {e}")

# --- 탭 2: HTML 파일 업로드 ---
with tab2:
    col1, col2 = st.columns(2)
    with col1:
        followers_upload = st.file_uploader("followers.html 업로드", type=['html'])
    with col2:
        following_upload = st.file_uploader("following.html 업로드", type=['html'])
        
    if followers_upload and following_upload:
        with st.spinner("데이터를 분석 중입니다..."):
            followers_df = parse_instagram_html(followers_upload.getvalue())
            following_df = parse_instagram_html(following_upload.getvalue())
        data_loaded = True
        st.success("데이터 추출 완료!")

st.divider()

# --- 예외 계정 처리 ---
deactivated_input = st.text_area(
    "🚫 분석에서 제외할 계정 (비활성화, 브랜드 등) - 선택사항", 
    placeholder="쉼표(,) 또는 줄바꿈으로 구분하여 입력하세요.\n예: stepblockkr, starbucks_korea"
)

# --- 분석 실행 및 결과 출력 ---
if data_loaded:
    if st.button("🚀 맞팔 분석 시작", use_container_width=True):
        # 1. 입력받은 예외 계정 리스트화
        deactivated_list = [x.strip() for x in deactivated_input.replace(',', '\n').split('\n') if x.strip()]
        
        # 2. Set 연산을 위한 데이터 변환
        followers_set = set(followers_df['Username'])
        following_set = set(following_df['Username'])
        deactivated_set = set(deactivated_list)
        
        # 3. 예외 계정을 제외한 순수 데이터 필터링
        filtered_following = following_set - deactivated_set
        filtered_followers = followers_set - deactivated_set
        
        # 4. 언팔로워(내가 팔로우하지만 나를 팔로우하지 않는 사람) 추출
        unfollowers = filtered_following - filtered_followers
        
        # --- 화면 표출 ---
        st.subheader("📊 데이터 요약")
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("총 팔로워", f"{len(filtered_followers)}명")
        col_b.metric("총 팔로잉", f"{len(filtered_following)}명")
        col_c.metric("나를 맞팔하지 않는 사람", f"{len(unfollowers)}명", delta="-언팔로워", delta_color="inverse")
        
        st.warning("""
        **⚠️ 분석 결과 확인 전 주의사항**
        * 메타(Meta) 서버의 백업 지연으로 최근 며칠 간의 팔로우 내역이 반영되지 않았을 수 있습니다.
        * 상대방이 계정을 일시 비활성화했거나, 삭제, 또는 차단한 경우 언팔로워로 분류됩니다. 직접 링크를 클릭해 확인하세요!
        """)
        
        st.divider()
        st.subheader("👀 나를 맞팔하지 않는 계정 목록")
        st.caption("표 안의 파란색 **인스타그램 아이디**를 클릭하면 해당 사용자의 프로필로 바로 이동합니다.")
        
        if unfollowers:
            # 클릭 가능한 프로필 링크 생성을 위한 데이터프레임 구성
            result_df = pd.DataFrame(
                [f"https://www.instagram.com/{user}/" for user in sorted(list(unfollowers))],
                columns=["Profile_URL"]
            )
            
            # LinkColumn을 활용하여 URL을 깔끔한 아이디 텍스트로 치환하여 렌더링
            st.dataframe(
                result_df,
                column_config={
                    "Profile_URL": st.column_config.LinkColumn(
                        "사용자 이름 (클릭 시 이동)",
                        display_text="https://www\\.instagram\\.com/([^/]+)/?"
                    )
                },
                hide_index=True,
                use_container_width=True
            )
            
            # 아이디 텍스트만 필요한 경우를 위해 복사 기능 제공
            with st.expander("📝 텍스트로 아이디만 복사하기"):
                sorted_usernames = sorted(list(unfollowers))
                st.code('\n'.join(sorted_usernames))
        else:
            st.balloons()
            st.success("모든 팔로잉 사용자가 회원님을 맞팔하고 있습니다! 🎉")
