import streamlit as st
from bs4 import BeautifulSoup
import pandas as pd
import zipfile

# 데이터를 캐싱하여 분석 속도를 높이고 반복 읽기 오류(EOF)를 방지합니다.
@st.cache_data
def parse_instagram_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    records = []
    
    for a_tag in soup.find_all('a'):
        href = a_tag.get('href', '')
        if 'instagram.com' in href:
            # URL에 쿼리 파라미터(?)가 붙어있을 경우를 대비해 순수 아이디만 추출
            username = href.split('?')[0].strip('/').split('/')[-1]
            
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

tab1, tab2 = st.tabs(["📦 ZIP 파일로 한 번에 업로드", "📄 HTML 파일 개별 업로드"])

followers_df = None
following_df = None
data_loaded = False

# 탭 1: ZIP 파일 업로드 로직
with tab1:
    st.info("💡 인스타그램에서 다운로드한 **.zip 파일**을 압축 해제하지 말고 그대로 올려주세요.")
    zip_file = st.file_uploader("ZIP 파일 업로드", type=['zip'], key='zip_upload')
    
    if zip_file is not None:
        try:
            with zipfile.ZipFile(zip_file) as z:
                followers_path = None
                following_path = None
                
                # 경로 탐색 버그 수정: 파일 이름 자체를 기준으로 정확히 매핑
                for f in z.namelist():
                    filename = f.split('/')[-1] # 순수 파일명만 추출
                    if filename.startswith('followers') and filename.endswith('.html'):
                        followers_path = f
                    elif filename.startswith('following') and filename.endswith('.html'):
                        following_path = f
                        
                if followers_path and following_path:
                    with st.spinner("ZIP 파일 데이터를 분석 중입니다..."):
                        followers_df = parse_instagram_html(z.read(followers_path))
                        following_df = parse_instagram_html(z.read(following_path))
                    data_loaded = True
                    st.success("데이터 추출 완료!")
                else:
                    st.error("ZIP 파일 내부에 팔로워/팔로잉 HTML 파일이 없습니다. 경로를 확인해주세요.")
        except Exception as e:
            st.error(f"ZIP 파일을 읽는 중 오류가 발생했습니다: {e}")

# 탭 2: 개별 HTML 파일 업로드 로직
with tab2:
    col1, col2 = st.columns(2)
    with col1:
        followers_upload = st.file_uploader("followers_1.html 업로드", type=['html'], key='follower_html')
    with col2:
        following_upload = st.file_uploader("following.html 업로드", type=['html'], key='following_html')
        
    if followers_upload and following_upload:
        with st.spinner("HTML 데이터를 분석 중입니다..."):
            # 파일 읽기 버그 수정: .read() 대신 .getvalue() 사용
            followers_df = parse_instagram_html(followers_upload.getvalue())
            following_df = parse_instagram_html(following_upload.getvalue())
        data_loaded = True
        st.success("데이터 추출 완료!")

st.divider()

# --- 비활성화 계정 필터링 및 분석 로직 ---
deactivated_input = st.text_area(
    "🚫 분석에서 제외할 계정 (비활성화 등) - 선택사항", 
    placeholder="쉼표(,) 또는 줄바꿈으로 구분하여 입력하세요.\n예: stepblockkr, user_abc"
)

# 데이터가 모두 로드되었을 때만 분석 실행 가능
if data_loaded:
    if st.button("🚀 맞팔 분석 시작", use_container_width=True):
        deactivated_list = [x.strip() for x in deactivated_input.replace(',', '\n').split('\n') if x.strip()]
        
        followers_set = set(followers_df['Username'])
        following_set = set(following_df['Username'])
        deactivated_set = set(deactivated_list)
        
        filtered_following = following_set - deactivated_set
        filtered_followers = followers_set - deactivated_set
        
        unfollowers = filtered_following - filtered_followers
        
        # --- 결과 화면 출력 ---
        st.subheader("📊 데이터 요약")
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("총 팔로워", f"{len(filtered_followers)}명")
        col_b.metric("총 팔로잉", f"{len(filtered_following)}명")
        col_c.metric("나를 맞팔하지 않는 사람", f"{len(unfollowers)}명", delta="-언팔로워", delta_color="inverse")
        
        # 💡여기에 경고 메시지 추가!
        st.warning("""
        **⚠️ 분석 결과 확인 전 주의사항**
        * 메타(Meta) 서버의 백업 지연으로 인해 **최근 며칠 간의 팔로우/언팔로우 내역이 반영되지 않았을 수 있습니다.**
        * 상대방이 계정을 **일시 비활성화했거나 영구 삭제, 또는 차단**한 경우 '맞팔하지 않는 계정'으로 분류될 수 있습니다.
        * 의심스러운 계정은 직접 인스타그램에서 한 번 더 확인하시는 것을 권장합니다.
        """)
        
        st.divider()
        st.subheader("👀 나를 맞팔하지 않는 계정 목록")
        
        if unfollowers:
            result_df = pd.DataFrame(list(unfollowers), columns=["Username"]).sort_values(by="Username").reset_index(drop=True)
            result_df.index = result_df.index + 1 
            st.dataframe(result_df, use_container_width=True)
            
            with st.expander("텍스트로 복사하기"):
                st.code('\n'.join(result_df['Username'].tolist()))
        else:
            st.balloons()
            st.success("모든 팔로잉 사용자가 회원님을 맞팔하고 있습니다! 🎉")
