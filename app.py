import streamlit as st
from bs4 import BeautifulSoup
import pandas as pd
import zipfile
import io

def parse_instagram_html(html_content):
    """HTML 콘텐츠(문자열 또는 바이트)를 받아 유저네임과 날짜를 추출하는 함수"""
    if not html_content:
        return pd.DataFrame(columns=['Username', 'Date'])
        
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

def extract_html_from_zip(zip_file):
    """ZIP 파일 내부를 탐색하여 팔로워 및 팔로잉 HTML 데이터를 추출하는 함수"""
    followers_bytes_list = []
    following_bytes = None
    
    # 메모리에서 ZIP 파일 읽기
    with zipfile.ZipFile(zip_file) as z:
        file_list = z.namelist()
        
        # 1. connections 폴더 내부의 following.html 찾기
        following_paths = [f for f in file_list if 'connections' in f and f.endswith('following.html')]
        if following_paths:
            with z.open(following_paths[0]) as f:
                following_bytes = f.read()
                
        # 2. connections 폴더 내부의 followers_로 시작하는 html 모두 찾기 
        # (팔로워가 많으면 followers_1.html, followers_2.html 등으로 쪼개지기 때문)
        followers_paths = [f for f in file_list if 'connections' in f and 'followers' in f and f.endswith('.html')]
        for path in sorted(followers_paths):
            with z.open(path) as f:
                followers_bytes_list.append(f.read())
                
    return followers_bytes_list, following_bytes

# --- 웹페이지 UI 구성 ---
st.set_page_config(page_title="인스타 맞팔 분석기", layout="centered")
st.title("📸 인스타그램 맞팔 분석기")
st.write("인스타그램에서 다운로드한 데이터를 이용해 나를 맞팔하지 않는 계정을 찾아보세요.")

# 업로드 방식 선택 (옵션 제공)
upload_mode = st.radio("업로드 방식 선택", ["ZIP 압축 파일 업로드 (추천)", "HTML 파일 개별 업로드"])

followers_data_list = []
following_data = None

if upload_mode == "ZIP 압축 파일 업로드 (추천)":
    zip_file = st.file_uploader("인스타그램 데이터 .zip 파일 업로드", type=['zip'])
    if zip_file:
        with st.spinner('ZIP 파일 내부 폴더를 탐색 중...'):
            followers_data_list, following_data = extract_html_from_zip(zip_file)
            if not following_data or not followers_data_list:
                st.error("ZIP 파일 내 'connections' 폴더에서 팔로워 또는 팔로잉 파일을 찾을 수 없습니다.")
                
else:
    col1, col2 = st.columns(2)
    with col1:
        f_file = st.file_uploader("팔로워 HTML 업로드 (followers_1.html)", type=['html'])
        if f_file:
            followers_data_list = [f_file.read()]
    with col2:
        fi_file = st.file_uploader("팔로잉 HTML 업로드 (following.html)", type=['html'])
        if fi_file:
            following_data = fi_file.read()

# 비활성화 계정 입력 텍스트 영역
deactivated_input = st.text_area(
    "분석에서 제외할 계정 (비활성화 등)", 
    placeholder="쉼표(,) 또는 줄바꿈으로 계정 ID를 구분하여 입력하세요."
)

# 분석 실행 버튼
if st.button("🚀 맞팔 분석 시작") and followers_data_list and following_data:
    deactivated_list = [x.strip() for x in deactivated_input.replace(',', '\n').split('\n') if x.strip()]
    
    with st.spinner('데이터 파싱 및 교차 분석 중...'):
        # 팔로잉 데이터 프레임 생성
        following_df = parse_instagram_html(following_data)
        
        # 팔로워 데이터 프레임 생성 (리스트 안의 모든 HTML 내용을 누적합산)
        followers_df_list = [parse_instagram_html(f_data) for f_data in followers_data_list]
        followers_df = pd.concat(followers_df_list, ignore_index=True).drop_duplicates() if followers_df_list else pd.DataFrame(columns=['Username', 'Date'])
        
        # Set 변환 및 필터링
        followers_set = set(followers_df['Username'])
        following_set = set(following_df['Username'])
        deactivated_set = set(deactivated_list)
        
        filtered_following = following_set - deactivated_set
        filtered_followers = followers_set - deactivated_set
        
        unfollowers = filtered_following - filtered_followers
        fans = filtered_followers - filtered_following
        
    st.success("분석이 완료되었습니다!")
    
    # 요약 카드 출력
    st.subheader("📊 데이터 요약")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("총 팔로워 (실소통)", f"{len(filtered_followers)}명")
    col_b.metric("총 팔로잉 (실소통)", f"{len(filtered_following)}명")
    col_c.metric("나를 맞팔 안 함", f"{len(unfollowers)}명", delta=f"-{len(unfollowers)}", delta_color="inverse")
    
    # 테이블 출력
    st.subheader("🔍 나를 맞팔하지 않는 계정 목록")
    if unfollowers:
        unfollowers_df = pd.DataFrame(list(unfollowers), columns=["사용자 이름(ID)"])
        st.dataframe(unfollowers_df, use_container_width=True, hide_index=True)
    else:
        st.info("🎉 축하합니다! 모든 팔로잉 사용자가 회원님을 맞팔하고 있습니다.")
