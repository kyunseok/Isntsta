import streamlit as st
from bs4 import BeautifulSoup
import pandas as pd
import zipfile

@st.cache_data
def parse_instagram_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    records = []
    
    for a_tag in soup.find_all('a'):
        href = a_tag.get('href', '')
        if 'instagram.com' in href:
            username = href.split('?')[0].strip('/').split('/')[-1]
            parent_div = a_tag.parent.parent
            if parent_div:
                divs = parent_div.find_all('div')
                date_str = divs[-1].text.strip() if len(divs) > 1 else ""
            else:
                date_str = ""
            records.append({'Username': username, 'Date': date_str})
            
    return pd.DataFrame(records).drop_duplicates()

st.set_page_config(page_title="인스타그램 맞팔 분석기", layout="centered")

st.title("🕵️‍♂️ 인스타그램 맞팔 분석기")
st.write("인스타그램 백업 데이터를 통해 나를 맞팔하지 않는 사람을 찾고, 클릭 한 번으로 프로필을 확인해 보세요.")

tab1, tab2 = st.tabs(["📦 ZIP 파일로 한 번에 업로드", "📄 HTML 파일 개별 업로드"])

followers_df = None
following_df = None
data_loaded = False

with tab1:
    st.info("💡 인스타그램에서 다운로드한 **.zip 파일**을 그대로 올려주세요.")
    zip_file = st.file_uploader("ZIP 파일 업로드", type=['zip'], key='zip_upload')
    
    if zip_file is not None:
        try:
            with zipfile.ZipFile(zip_file) as z:
                followers_path = next((f for f in z.namelist() if f.split('/')[-1].startswith('followers') and f.endswith('.html')), None)
                following_path = next((f for f in z.namelist() if f.split('/')[-1].startswith('following') and f.endswith('.html')), None)
                        
                if followers_path and following_path:
                    with st.spinner("데이터를 분석 중입니다..."):
                        followers_df = parse_instagram_html(z.read(followers_path))
                        following_df = parse_instagram_html(z.read(following_path))
                    data_loaded = True
                    st.success("데이터 추출 완료!")
                else:
                    st.error("ZIP 파일 내부에 팔로워/팔로잉 HTML 파일이 없습니다. 경로를 확인해주세요.")
        except Exception as e:
            st.error(f"오류 발생: {e}")

with tab2:
    col1, col2 = st.columns(2)
    with col1:
        followers_upload = st.file_uploader("followers.html", type=['html'])
    with col2:
        following_upload = st.file_uploader("following.html", type=['html'])
        
    if followers_upload and following_upload:
        followers_df = parse_instagram_html(followers_upload.getvalue())
        following_df = parse_instagram_html(following_upload.getvalue())
        data_loaded = True
        st.success("데이터 추출 완료!")

st.divider()

deactivated_input = st.text_area(
    "🚫 분석에서 제외할 계정 (비활성화 등) - 선택사항", 
    placeholder="쉼표(,) 또는 줄바꿈으로 구분하여 입력하세요.\n예: stepblockkr, user_abc"
)

if data_loaded:
    if st.button("🚀 맞팔 분석 시작", use_container_width=True):
        deactivated_list = [x.strip() for x in deactivated_input.replace(',', '\n').split('\n') if x.strip()]
        
        followers_set = set(followers_df['Username'])
        following_set = set(following_df['Username'])
        deactivated_set = set(deactivated_list)
        
        filtered_following = following_set - deactivated_set
        filtered_followers = followers_set - deactivated_set
        
        unfollowers = filtered_following - filtered_followers
        
        st.subheader("📊 데이터 요약")
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("총 팔로워", f"{len(filtered_followers)}명")
        col_b.metric("총 팔로잉", f"{len(filtered_following)}명")
        col_c.metric("나를 맞팔하지 않는 사람", f"{len(unfollowers)}명", delta="-언팔로워", delta_color="inverse")
        
        st.warning("""
        **⚠️ 주의사항**
        * 메타 서버 지연으로 최근 내역이 반영되지 않았을 수 있습니다.
        * 계정을 비활성화/삭제/차단한 경우 언팔로워로 뜰 수 있습니다. 아래 링크를 클릭해 직접 확인해 보세요!
        """)
        
        st.divider()
        st.subheader("👀 나를 맞팔하지 않는 계정 목록")
        st.caption("표 안의 **'프로필 링크'**를 클릭하면 해당 사용자의 인스타그램으로 바로 이동합니다.")
        
        if unfollowers:
            # 1. 데이터프레임 생성 및 정렬
            result_df = pd.DataFrame(list(unfollowers), columns=["Username"]).sort_values(by="Username").reset_index(drop=True)
            
            # 2. 프로필 주소 컬럼 추가
            result_df["Profile_URL"] = result_df["Username"].apply(lambda x: f"https://www.instagram.com/{x}/")
            
            # 3. Streamlit에 테이블 렌더링 (LinkColumn 적용)
            st.dataframe(
                result_df,
                column_config={
                    "Username": "인스타그램 아이디",
                    "Profile_URL": st.column_config.LinkColumn(
                        "프로필 방문하기", 
                        display_text="🔗 프로필 열기" # 화면에 보일 텍스트
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
