import streamlit as st
from bs4 import BeautifulSoup
import pandas as pd
import zipfile

def parse_instagram_html(html_content):
    """HTML 텍스트(문자열/바이트)를 받아 파싱하는 함수"""
    soup = BeautifulSoup(html_content, 'html.parser')
    records = []
    
    for a_tag in soup.find_all('a'):
        href = a_tag.get('href', '')
        if 'instagram.com' in href:
            username = href.strip('/').split('/')[-1]
            parent_div = a_tag.parent.parent
            if parent_div:
                divs = parent_div.find_all('div')
                date_str = divs[-1].text.strip() if len(divs) > 1 else ""
            else:
                date_str = ""
            records.append({'Username': username, 'Date': date_str})
            
    return pd.DataFrame(records).drop_duplicates()

# --- 웹페이지 UI 구성 ---
st.set_page_config(page_title="인스타그램 맞팔 분석기", layout="centered")
st.title("🕵️‍♂️ 인스타그램 맞팔 분석기")
st.write("인스타그램에서 다운로드한 백업 데이터를 통해 나를 맞팔하지 않는 사람을 찾아보세요.")

# 분석 옵션 탭 생성
tab1, tab2 = st.tabs(["📦 ZIP 파일로 한 번에 업로드", "📄 HTML 파일 개별 업로드"])

followers_df = None
following_df = None
data_loaded = False

# 탭 1: ZIP 파일 업로드
with tab1:
    st.info("💡 인스타그램에서 다운로드한 **.zip 파일**을 압축 해제하지 말고 그대로 올려주세요.")
    zip_file = st.file_uploader("ZIP 파일 업로드", type=['zip'], key='zip_upload')
    
    if zip_file is not None:
        try:
            with zipfile.ZipFile(zip_file) as z:
                file_names = z.namelist()
                
                # connections/followers_and_following 경로 내의 파일 찾기
                followers_path = next((f for f in file_names if 'followers_and_following' in f and 'followers' in f and f.endswith('.html')), None)
                following_path = next((f for f in file_names if 'followers_and_following' in f and 'following.html' in f), None)
                
                if followers_path and following_path:
                    # 메모리에서 바로 읽어오기
                    followers_html = z.read(followers_path).decode('utf-8')
                    following_html = z.read(following_path).decode('utf-8')
                    
                    with st.spinner("ZIP 파일 안의 데이터를 추출 중입니다..."):
                        followers_df = parse_instagram_html(followers_html)
                        following_df = parse_instagram_html(following_html)
                    
                    st.success("ZIP 파일에서 팔로워/팔로잉 데이터를 성공적으로 추출했습니다!")
                    data_loaded = True
                else:
                    st.error("ZIP 파일 내부에 팔로워/팔로잉 HTML 파일이 없습니다. 올바른 인스타그램 백업 파일인지 확인해주세요.")
        except Exception as e:
            st.error(f"ZIP 파일을 읽는 중 오류가 발생했습니다: {e}")

# 탭 2: 개별 HTML 업로드
with tab2:
    st.write("또는 기존 방식대로 HTML 파일을 각각 업로드할 수 있습니다.")
    col1, col2 = st.columns(2)
    with col1:
        followers_upload = st.file_uploader("followers_1.html 업로드", type=['html'], key='follower_html')
    with col2:
        following_upload = st.file_uploader("following.html 업로드", type=['html'], key='following_html')
        
    if followers_upload and following_upload and not data_loaded:
        with st.spinner("HTML 데이터를 추출 중입니다..."):
            followers_df = parse_instagram_html(followers_upload.read())
            following_df = parse_instagram_html(following_upload.read())
        st.success("HTML 데이터를 성공적으로 추출했습니다!")
        data_loaded = True

st.divider()

# --- 비활성화 계정 필터링 및 분석 로직 ---
deactivated_input = st.text_area(
    "🚫 분석에서 제외할 계정 (비활성화 등) - 선택사항", 
    placeholder="쉼표(,) 또는 줄바꿈으로 구분하여 입력하세요.\n예: stepblockkr, __deleted__123"
)

# 데이터가 성공적으로 로드된 경우에만 분석 버튼 활성화
if data_loaded:
    if st.button("🚀 맞팔 분석 시작", use_container_width=True):
        deactivated_list = [x.strip() for x in deactivated_input.replace(',', '\n').split('\n') if x.strip()]
        
        followers_set = set(followers_df['Username'])
        following_set = set(following_df['Username'])
        deactivated_set = set(deactivated_list)
        
        filtered_following = following_set - deactivated_set
        filtered_followers = followers_set - deactivated_set
        
        unfollowers = filtered_following - filtered_followers
        fans = filtered_followers - filtered_following
        mutuals = filtered_following & filtered_followers
        
        # --- 결과 화면 ---
        st.subheader("📊 데이터 요약")
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("총 팔로워", f"{len(filtered_followers)}명")
        col_b.metric("총 팔로잉", f"{len(filtered_following)}명")
        col_c.metric("나를 맞팔하지 않는 사람", f"{len(unfollowers)}명", delta="-언팔로워", delta_color="inverse")
        
        st.divider()
        st.subheader("👀 나를 맞팔하지 않는 계정 목록")
        
        if unfollowers:
            # 보기 편하게 데이터프레임으로 출력 (정렬 추가)
            result_df = pd.DataFrame(list(unfollowers), columns=["Username"]).sort_values(by="Username").reset_index(drop=True)
            # 인덱스를 1부터 시작하도록 조정
            result_df.index = result_df.index + 1 
            st.dataframe(result_df, use_container_width=True)
            
            # 카피하기 쉬운 텍스트 형태로도 제공
            with st.expander("텍스트로 복사하기"):
                st.code('\n'.join(result_df['Username'].tolist()))
        else:
            st.balloons()
            st.success("모든 팔로잉 사용자가 회원님을 맞팔하고 있습니다! 🎉")
