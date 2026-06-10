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
            username = href.split('?')[0].strip('/').split('/')[-1]
            
            parent_div = a_tag.parent.parent
            date_str = ""
            parsed_date = pd.NaT # 정렬을 위한 기본 빈 날짜값
            
            if parent_div:
                divs = parent_div.find_all('div')
                if len(divs) > 1:
                    raw_date = divs[-1].text.strip()
                    
                    try:
                        # 텍스트 분리 및 시간 계산
                        parts = raw_date.replace(',', '').split()
                        if len(parts) >= 5:
                            month = int(parts[0].replace('월', ''))
                            day = int(parts[1])
                            year = int(parts[2])
                            hour, minute = map(int, parts[3].split(':'))
                            ampm = parts[4]
                            
                            # 화면 표출용 친절한 텍스트
                            date_str = f"{year}년 {month}월 {day}일 {ampm} {hour}시 {minute}분"
                            
                            # 컴퓨터 정렬용 24시간제 변환
                            calc_hour = hour
                            if ampm == '오후' and hour != 12:
                                calc_hour += 12
                            elif ampm == '오전' and hour == 12:
                                calc_hour = 0
                                
                            # 정렬을 위한 실제 Timestamp 객체 생성
                            parsed_date = pd.Timestamp(year, month, day, calc_hour, minute)
                        else:
                            date_str = raw_date
                    except Exception:
                        date_str = raw_date
                    
            # 화면 표시용(Date)과 정렬용(Parsed_Date)을 함께 저장
            records.append({'Username': username, 'Date': date_str, 'Parsed_Date': parsed_date})
            
    return pd.DataFrame(records).drop_duplicates(subset=['Username'])

st.set_page_config(page_title="인스타그램 맞팔 분석기", page_icon="🕵️‍♂️", layout="centered")

st.title("🕵️‍♂️ 인스타그램 맞팔 분석기")
st.write("인스타그램 백업 데이터를 통해 나를 맞팔하지 않는 사람을 찾고, 팔로우 시작 날짜도 함께 확인해 보세요.")

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
        **⚠️ 분석 결과 확인 전 주의사항**
        * 메타(Meta) 서버의 백업 지연으로 최근 며칠 간의 팔로우 내역이 반영되지 않았을 수 있습니다.
        * 상대방이 계정을 일시 비활성화했거나, 삭제, 또는 차단한 경우 언팔로워로 분류됩니다. 직접 링크를 클릭해 확인하세요!
        """)
        
        st.divider()
        st.subheader("👀 나를 맞팔하지 않는 계정 목록")
        st.caption("표 안의 파란색 **인스타그램 아이디**를 클릭하면 해당 사용자의 프로필로 바로 이동합니다.")
        
        if unfollowers:
            result_df = following_df[following_df['Username'].isin(unfollowers)].copy()
            result_df["Profile_URL"] = result_df["Username"].apply(lambda x: f"https://www.instagram.com/{x}/")
            
            # [추가됨] 정렬 방식을 선택하는 라디오 버튼 UI
            sort_order = st.radio(
                "📅 날짜 정렬 방식",
                ["오래된 순 (오름차순)", "최신 순 (내림차순)"],
                horizontal=True
            )
            
            # 선택한 방식에 따라 Parsed_Date(실제 시간 데이터)를 기준으로 정렬 수행
            is_ascending = True if sort_order == "오래된 순 (오름차순)" else False
            result_df = result_df.sort_values(by="Parsed_Date", ascending=is_ascending, na_position='last').reset_index(drop=True)
            
            # 출력 시에는 숨겨진 Parsed_Date를 빼고 Profile_URL과 문자열 Date만 표출
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
