import streamlit as st
from bs4 import BeautifulSoup
import pandas as pd
import zipfile

# 세션 상태 초기화
if 'analyzed' not in st.session_state:
    st.session_state['analyzed'] = False

def reset_analysis():
    st.session_state['analyzed'] = False

@st.cache_data
def parse_instagram_html(html_content):
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

st.set_page_config(page_title="인스타그램 맞팔 분석기", page_icon="🕵️‍♂️", layout="centered")

#########
### UI
#########

st.title("Isntsta")
st.write("내가 팔로우하고 있는 상대방이 나를 팔로우하고 있지 않을까요?")

tab1, tab2 = st.tabs(["📦 ZIP 파일로 한 번에 업로드", "📄 HTML 파일 개별 업로드"])

followers_df = None
following_df = None
data_loaded = False

# --- 탭 1: ZIP 파일 업로드 ---
with tab1:
    st.info("💡 인스타그램에서 다운로드한 **.zip 파일**을 압축 해제하지 말고 그대로 올려주세요.")
    zip_file = st.file_uploader("ZIP 파일 업로드", type=['zip'], key='zip_upload', on_change=reset_analysis)
    
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
                else:
                    st.error("파일이 유효하지 않습니다.")
        except Exception as e: #에러 내용 일부러 숨기는거임
            st.error(f"오류 발생가 발생했습니다.")

# --- 탭 2: HTML 파일 개별 업로드 ---
with tab2:
    col1, col2 = st.columns(2)
    with col1:
        followers_upload = st.file_uploader("followers.html 업로드", type=['html'], key='followers_indiv', on_change=reset_analysis)
    with col2:
        following_upload = st.file_uploader("following.html 업로드", type=['html'], key='following_indiv', on_change=reset_analysis)
        
    if followers_upload and following_upload:
        with st.spinner("데이터를 분석 중입니다..."):
            followers_df = parse_instagram_html(followers_upload.getvalue())
            following_df = parse_instagram_html(following_upload.getvalue())
        data_loaded = True

st.divider()

deactivated_input = st.text_area(
    "🚫 분석에서 제외할 계정 (비활성화, 브랜드, 대형 크리에이터 계정 등) - 선택사항", 
    placeholder="쉼표(,) 또는 줄바꿈으로 구분하여 입력하세요.\n예: gov_korea, k_yseok.07"
)

if data_loaded:
    if st.button("🚀 맞팔 분석 시작", use_container_width=True):
        deactivated_list = [x.strip() for x in deactivated_input.replace(',', '\n').split('\n') if x.strip()]
        
        followers_set = set(followers_df['Username'])
        following_set = set(following_df['Username'])
        deactivated_set = set(deactivated_list)
        
        st.session_state['filtered_following'] = following_set - deactivated_set
        st.session_state['filtered_followers'] = followers_set - deactivated_set
        st.session_state['unfollowers'] = st.session_state['filtered_following'] - st.session_state['filtered_followers']
        st.session_state['analyzed'] = True

    if st.session_state['analyzed']:
        unfollowers = st.session_state['unfollowers']
        filtered_followers = st.session_state['filtered_followers']
        filtered_following = st.session_state['filtered_following']
        
        st.subheader("📊 데이터 요약")
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("총 팔로워", f"{len(filtered_followers)}명")
        # 데이터 파일 상의 총 팔로잉 수를 명시적으로 보여줌
        col_b.metric("데이터상 총 팔로잉", f"{len(filtered_following)}명")
        col_c.metric("나를 맞팔하지 않는 사람", f"{len(unfollowers)}명", delta="-언팔로워", delta_color="inverse")
        
        st.warning("""
        **⚠️ Isntsta 사용 전 주의사항**
        * 특정 계정이 비활성화, 삭제, 정지된 경우 인앱에서 확인되는 팔로워/팔로잉 수가 위 숫자와 다를 수 있습니다.
        * 아래 표는 참고용일 뿐, 실제 결과는 직접 확인하여 주시기 바랍니다.
        """)
        
        st.divider()
        st.subheader("👀 분석 결과")
        st.caption("**인스타그램 아이디**를 클릭하면 해당 프로필로 이동합니다. **컬럼 제목을 클릭하여 정렬 방식을 바꿀 수 있습니다.**")
        
        if unfollowers:
            result_df = following_df[following_df['Username'].isin(unfollowers)].copy()
            result_df["Profile_URL"] = result_df["Username"].apply(lambda x: f"https://www.instagram.com/{x}/")
            
            # 기본적으로 컴퓨터가 인식할 수 있는 날짜(Parsed_Date) 기준으로 '오래된 순(True)' 정렬 수행
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
