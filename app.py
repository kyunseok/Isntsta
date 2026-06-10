import streamlit as st
import streamlit.components.v1 as components
from bs4 import BeautifulSoup
import pandas as pd
import zipfile
import requests
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

def fetch_follower_count(username):
    # 인스타그램 비공식 Web API 사용 (로그인 리다이렉트 방지 및 정확한 숫자 추출)
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "X-IG-App-ID": "936619743392459",  # 인스타그램 웹 클라이언트 인증 ID
        "Accept": "*/*"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            # JSON 구조에서 팔로워 수 정수값만 정확하게 파싱
            return int(data['data']['user']['edge_followed_by']['count'])
    except Exception:
        pass
    
    return -1

st.set_page_config(page_title="인스타그램 맞팔 분석기", layout="centered")

# 브라우저 알림 권한을 미리 요청하는 자바스크립트 주입
components.html("""
    <script>
    if (Notification.permission !== "granted" && Notification.permission !== "denied") {
        Notification.requestPermission();
    }
    </script>
""", height=0, width=0)

st.title("인스타그램 맞팔 분석기")
st.write("인스타그램에서 다운로드한 백업 데이터를 통해 나를 맞팔하지 않는 사람을 찾아보세요.")

tab1, tab2 = st.tabs(["ZIP 파일로 한 번에 업로드", "HTML 파일 개별 업로드"])

followers_df = None
following_df = None
data_loaded = False

with tab1:
    st.info("인스타그램에서 다운로드한 .zip 파일을 압축 해제하지 말고 그대로 올려주세요.")
    zip_file = st.file_uploader("ZIP 파일 업로드", type=['zip'], key='zip_upload')
    
    if zip_file is not None:
        try:
            with zipfile.ZipFile(zip_file) as z:
                followers_path = None
                following_path = None
                
                for f in z.namelist():
                    filename = f.split('/')[-1]
                    if filename.startswith('followers') and filename.endswith('.html'):
                        followers_path = f
                    elif filename.startswith('following') and filename.endswith('.html'):
                        following_path = f
                        
                if followers_path and following_path:
                    with st.spinner("ZIP 파일 데이터를 분석 중입니다..."):
                        followers_df = parse_instagram_html(z.read(followers_path))
                        following_df = parse_instagram_html(z.read(following_path))
                    data_loaded = True
                    st.success("데이터 추출 완료")
                else:
                    st.error("ZIP 파일 내부에 팔로워/팔로잉 HTML 파일이 없습니다. 경로를 확인해주세요.")
        except Exception as e:
            st.error(f"ZIP 파일을 읽는 중 오류가 발생했습니다: {e}")

with tab2:
    col1, col2 = st.columns(2)
    with col1:
        followers_upload = st.file_uploader("followers_1.html 업로드", type=['html'], key='follower_html')
    with col2:
        following_upload = st.file_uploader("following.html 업로드", type=['html'], key='following_html')
        
    if followers_upload and following_upload:
        with st.spinner("HTML 데이터를 분석 중입니다..."):
            followers_df = parse_instagram_html(followers_upload.getvalue())
            following_df = parse_instagram_html(following_upload.getvalue())
        data_loaded = True
        st.success("데이터 추출 완료")

st.divider()

deactivated_input = st.text_area(
    "분석에서 제외할 계정 (비활성화 등) - 선택사항", 
    placeholder="쉼표(,) 또는 줄바꿈으로 구분하여 입력하세요.\n예: stepblockkr, user_abc"
)

if data_loaded:
    if st.button("맞팔 분석 시작", use_container_width=True):
        deactivated_list = [x.strip() for x in deactivated_input.replace(',', '\n').split('\n') if x.strip()]
        
        followers_set = set(followers_df['Username'])
        following_set = set(following_df['Username'])
        deactivated_set = set(deactivated_list)
        
        filtered_following = following_set - deactivated_set
        filtered_followers = followers_set - deactivated_set
        
        unfollowers = filtered_following - filtered_followers
        
        st.session_state['unfollowers'] = list(unfollowers)
        
        st.subheader("데이터 요약")
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("총 팔로워", f"{len(filtered_followers)}명")
        col_b.metric("총 팔로잉", f"{len(filtered_following)}명")
        col_c.metric("나를 맞팔하지 않는 사람", f"{len(unfollowers)}명", delta="-언팔로워", delta_color="inverse")
        
        st.warning("""
        주의사항
        * 메타 서버의 백업 지연으로 인해 최근 며칠 간의 팔로우 내역이 반영되지 않았을 수 있습니다.
        * 상대방이 계정을 일시 비활성화했거나 영구 삭제, 또는 차단한 경우 맞팔하지 않는 계정으로 분류될 수 있습니다.
        """)
        
        st.divider()
        st.subheader("나를 맞팔하지 않는 계정 목록")
        
        if unfollowers:
            result_df = pd.DataFrame(list(unfollowers), columns=["Username"]).sort_values(by="Username").reset_index(drop=True)
            result_df.index = result_df.index + 1 
            st.dataframe(result_df, use_container_width=True)
        else:
            st.success("모든 팔로잉 사용자가 회원님을 맞팔하고 있습니다.")

    if 'unfollowers' in st.session_state and st.session_state['unfollowers']:
        st.divider()
        st.subheader("크리에이터 계정 분리")
        st.write("맞팔하지 않는 계정 중, 팔로워가 일정 수 이상인 유명인이나 크리에이터를 검색하여 별도로 분류합니다.")
        
        threshold = st.number_input("크리에이터 기준 팔로워 수", min_value=100, value=1000, step=100)
        
        if st.button("크리에이터 분류 실행 (주의: 시간이 소요됩니다)"):
            unfollowers_list = st.session_state['unfollowers']
            total = len(unfollowers_list)
            
            creator_list = []
            normal_unfollowers = []
            error_list = []
            
            progress_bar = st.progress(0, text="크롤링을 준비 중입니다...")
            
            for i, user in enumerate(unfollowers_list):
                progress_bar.progress((i) / total, text=f"[{i+1}/{total}] {user} 계정 분석 중...")
                
                count = fetch_follower_count(user)
                time.sleep(1.5)
                
                if count == -1:
                    error_list.append(user)
                    normal_unfollowers.append(user)
                elif count >= threshold:
                    creator_list.append({"Username": user, "Followers": count})
                else:
                    normal_unfollowers.append(user)
                    
            progress_bar.progress(1.0, text="크롤링 완료")
            
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.markdown("#### 크리에이터 계정")
                if creator_list:
                    creator_df = pd.DataFrame(creator_list).sort_values(by="Followers", ascending=False).reset_index(drop=True)
                    creator_df.index = creator_df.index + 1
                    st.dataframe(creator_df, use_container_width=True)
                else:
                    st.info("조건에 맞는 크리에이터가 없습니다.")
                    
            with col_right:
                st.markdown("#### 일반 지인 언팔로워")
                if normal_unfollowers:
                    normal_df = pd.DataFrame(normal_unfollowers, columns=["Username"]).sort_values(by="Username").reset_index(drop=True)
                    normal_df.index = normal_df.index + 1
                    st.dataframe(normal_df, use_container_width=True)
                else:
                    st.info("모두 크리에이터 계정입니다.")
                    
            if error_list:
                st.warning(f"접근 차단 또는 비공개로 인해 팔로워 수를 확인하지 못한 계정이 {len(error_list)}개 있습니다. 이들은 일반 지인 목록으로 분류되었습니다.")
            
            # 크롤링 완료 시 브라우저 푸시 알림 실행
            components.html("""
                <script>
                if (Notification.permission === "granted") {
                    new Notification("분석 완료", {
                        body: "크리에이터 분류 작업이 성공적으로 끝났습니다. 브라우저로 돌아와 결과를 확인하세요!"
                    });
                }
                </script>
            """, height=0, width=0)
