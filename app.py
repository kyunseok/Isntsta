import streamlit as st
from bs4 import BeautifulSoup
import pandas as pd

def parse_instagram_html(uploaded_file):
    # 업로드된 파일 객체를 읽어 파싱
    soup = BeautifulSoup(uploaded_file, 'html.parser')
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

# 웹페이지 UI 구성
st.title("인스타그램 맞팔 분석기")
st.write("다운로드한 팔로워 및 팔로잉 HTML 파일을 업로드하여 나를 맞팔하지 않는 계정을 찾아보세요.")

# 파일 업로드 위젯
col1, col2 = st.columns(2)
with col1:
    followers_file = st.file_uploader("팔로워 HTML 업로드", type=['html'])
with col2:
    following_file = st.file_uploader("팔로잉 HTML 업로드", type=['html'])

# 비활성화 계정 입력 텍스트 영역
deactivated_input = st.text_area(
    "분석에서 제외할 계정 (비활성화 등)", 
    placeholder="쉼표(,) 또는 줄바꿈으로 구분하여 입력하세요.\n예시: __deleted__123, user_abc"
)

# 분석 실행 버튼
if st.button("분석 시작") and followers_file and following_file:
    # 예외 계정 리스트화
    deactivated_list = [x.strip() for x in deactivated_input.replace(',', '\n').split('\n') if x.strip()]
    
    # 데이터 파싱
    with st.spinner('데이터를 분석 중입니다...'):
        followers_df = parse_instagram_html(followers_file)
        following_df = parse_instagram_html(following_file)
        
        followers_set = set(followers_df['Username'])
        following_set = set(following_df['Username'])
        deactivated_set = set(deactivated_list)
        
        filtered_following = following_set - deactivated_set
        filtered_followers = followers_set - deactivated_set
        
        unfollowers = filtered_following - filtered_followers
        fans = filtered_followers - filtered_following
        mutuals = filtered_following & filtered_followers
        
    st.success("분석 완료!")
    
    # 결과 요약 지표 출력
    st.subheader("데이터 요약")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("총 팔로워", f"{len(filtered_followers)}명")
    col_b.metric("총 팔로잉", f"{len(filtered_following)}명")
    col_c.metric("맞팔 안 한 사람", f"{len(unfollowers)}명")
    
    # 결과 리스트 출력
    st.subheader("나를 맞팔하지 않는 계정")
    if unfollowers:
        st.dataframe(pd.DataFrame(list(unfollowers), columns=["Username"]), use_container_width=True)
    else:
        st.info("모든 팔로잉 사용자가 회원님을 맞팔하고 있습니다.")