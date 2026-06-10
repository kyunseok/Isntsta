import streamlit as st
from bs4 import BeautifulSoup
import pandas as pd
import zipfile
import requests
import urllib.parse
import time

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

def fetch_follower_count_api(username):
    url = "https://instagram-scraper-stable-api.p.rapidapi.com/get_ig_user_followers_v2.php"
    
    try:
        # st.secrets를 통해 숨겨둔 API 키를 안전하게 불러옵니다.
        api_key = st.secrets["RAPIDAPI_KEY"]
        api_host = st.secrets["RAPIDAPI_HOST"]
    except Exception:
        return -2 # secrets.toml 파일이 없거나 설정되지 않음
        
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": api_host,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    # URL 인코딩 처리
    encoded_url = urllib.parse.quote_plus(f"https://www.instagram.com/{username}/")
    payload = f"username_or_url={encoded_url}&data=followers&amount=12&pagination_token="
    
    try:
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            # API 응답 JSON에서 총 팔로워 수 추출
            # 참고: 사용하는 API의 실제 JSON 응답 구조에 따라 키 이름이 달라질 수 있습니다.
            try:
                # 일반적인 메타데이터 구조 가정
                return int(data["data"]["user"]["edge_followed_by"]["count"])
            except KeyError:
                # 응답 구조가 다를 경우를 대비한 안전 장치
                return -1
    except Exception:
        pass
        
    return -1

st.set_page_config(page_title="인스타그램 맞팔 분석기", layout="centered")

st.title("인스타그램 맞팔 분석기")
st.write("인스타그램 백업 데이터를 통해 나를 맞팔하지 않는 사람을 찾고 크리에이터를 분류합니다.")

tab1, tab2 = st.tabs(["ZIP 파일로 업로드", "HTML 파일 개별 업로드"])

followers_df = None
following_df = None
data_loaded = False

with tab1:
    zip_file = st.file_uploader("ZIP 파일 업로드", type=['zip'], key='zip_upload')
    if zip_file is not None:
        try:
            with zipfile.ZipFile(zip_file) as z:
                followers_path = next((f for f in z.namelist() if f.split('/')[-1].startswith('followers') and f.endswith('.html')), None)
                following_path = next((f for f in z.namelist() if f.split('/')[-1].startswith('following') and f.endswith('.html')), None)
                        
                if followers_path and following_path:
                    with st.spinner("데이터 분석 중..."):
                        followers_df = parse_instagram_html(z.read(followers_path))
                        following_df = parse_instagram_html(z.read(following_path))
                    data_loaded = True
        except Exception:
            st.error("파일 처리 중 오류가 발생했습니다.")

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

st.divider()

if data_loaded:
    if st.button("맞팔 분석 시작", use_container_width=True):
        followers_set = set(followers_df['Username'])
        following_set = set(following_df['Username'])
        
        unfollowers = following_set - followers_set
        st.session_state['unfollowers'] = list(unfollowers)
        
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("총 팔로워", f"{len(followers_set)}명")
        col_b.metric("총 팔로잉", f"{len(following_set)}명")
        col_c.metric("나를 맞팔하지 않는 사람", f"{len(unfollowers)}명")
        
        st.divider()
        st.subheader("나를 맞팔하지 않는 계정 목록")
        
        if unfollowers:
            result_df = pd.DataFrame(
                [f"https://www.instagram.com/{user}/" for user in sorted(list(unfollowers))],
                columns=["Profile_URL"]
            )
            
            st.dataframe(
                result_df,
                column_config={
                    "Profile_URL": st.column_config.LinkColumn(
                        "사용자 이름 (클릭 시 프로필 이동)",
                        display_text="https://www\\.instagram\\.com/([^/]+)/?"
                    )
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.success("모든 팔로잉 사용자가 회원님을 맞팔하고 있습니다.")

    if 'unfollowers' in st.session_state and st.session_state['unfollowers']:
        st.divider()
        st.subheader("크리에이터 계정 분리 (RapidAPI 연동)")
        
        threshold = st.number_input("크리에이터 기준 팔로워 수", min_value=100, value=1000, step=100)
        
        if st.button("자동 분류 실행"):
            unfollowers_list = st.session_state['unfollowers']
            total = len(unfollowers_list)
            
            creator_list = []
            normal_unfollowers = []
            error_list = []
            
            progress_bar = st.progress(0, text="API 호출 준비 중...")
            
            for i, user in enumerate(unfollowers_list):
                progress_bar.progress((i) / total, text=f"{i+1}/{total} - {user} 계정 조회 중...")
                
                count = fetch_follower_count_api(user)
                
                if count == -2:
                    st.error(".streamlit/secrets.toml 파일에 API 키가 설정되지 않았습니다.")
                    st.stop()
                elif count == -1:
                    error_list.append(user)
                    normal_unfollowers.append(user)
                elif count >= threshold:
                    creator_list.append({"Username": user, "Followers": count})
                else:
                    normal_unfollowers.append(user)
                
                # 무료 API 요금제 제한(Rate Limit)을 피하기 위한 딜레이
                time.sleep(1.0)
                    
            progress_bar.progress(1.0, text="분류 완료")
            
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.markdown("#### 크리에이터 계정")
                if creator_list:
                    st.dataframe(pd.DataFrame(creator_list).sort_values(by="Followers", ascending=False).reset_index(drop=True), use_container_width=True)
                else:
                    st.info("조건에 맞는 계정이 없습니다.")
                    
            with col_right:
                st.markdown("#### 일반 지인")
                if normal_unfollowers:
                    st.dataframe(pd.DataFrame(normal_unfollowers, columns=["Username"]).reset_index(drop=True), use_container_width=True)
                    
            if error_list:
                st.warning("일부 계정의 정보를 불러오지 못해 일반 목록으로 분류되었습니다.")
