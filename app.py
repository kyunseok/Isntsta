import streamlit as st
import pandas as pd
import zipfile
import os
import base64

from dataParser import InstagramDataParser
from analyzer import InstagramAnalyzer

def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

class InstagramAppUI:
    def __init__(self):
        self.setup_page()
        self.init_session_state()

    def setup_page(self):
        st.set_page_config(page_title="Isntsta", page_icon="🕵️‍♂️", layout="centered")

    def init_session_state(self):
        if 'analyzed' not in st.session_state:
            st.session_state['analyzed'] = False
        if 'data_loaded' not in st.session_state:
            st.session_state['data_loaded'] = False
        if 'instruction_step' not in st.session_state:
            st.session_state['instruction_step'] = 1

    def reset_analysis(self):
        st.session_state['analyzed'] = False
        st.session_state['data_loaded'] = False

    def next_step(self):
        if st.session_state['instruction_step'] < 4:
            st.session_state['instruction_step'] += 1

    def prev_step(self):
        if st.session_state['instruction_step'] > 1:
            st.session_state['instruction_step'] -= 1

    def run(self):
        logo_b64 = get_base64_image("logo.png")
        if logo_b64:
            # 로고 크기는 4.5rem 유지
            logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="height: 4.5rem; margin-right: 20px; border-radius: 15px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1);">'
        else:
            logo_html = '<span style="font-size: 4.5rem; margin-right: 20px;">🕵️‍♂️</span>'

        st.markdown(f"""
        <style>
        .title-container {{
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }}
        .insta-title {{
            background: -webkit-linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 900 !important;
            font-size: 4.5rem !important; /* 글씨 크기만 6rem에서 4.5rem으로 낮춤 */
            margin-bottom: 0px !important;
            padding-bottom: 0px !important;
            line-height: 1.1 !important;
        }}
        .insta-subtitle {{
            background: -webkit-linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: bold;
            text-align: center;
            margin-bottom: 15px;
        }}
        /* 중앙 버튼 스타일 개선 */
        .stButton>button {{
            height: 100%;
            font-size: 1.5rem;
        }}
        </style>
        <div class="title-container">
            {logo_html}
            <div class="insta-title">Isntsta</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("나를 맞팔하지 않는 계정을 안전하고 빠르게 찾아보세요.")
        
        tab1, tab2, tab3, tab4 = st.tabs(["About", "사용 방법", "📦 ZIP 파일 업로드", "Developer"])

        with tab1:
            self.render_about_app_section()

        with tab2:
            self.render_instructions()

        with tab3:
            self.render_upload_section()
            self.render_analysis_section()
            
        with tab4:
            self.render_developer_section()

    def render_about_app_section(self):
        st.subheader("Isntsta란?")
        st.markdown("""
        **Isntsta**는 귀찮은 회원가입이나 결제 없이도 인스타그램에서 **나를 팔로우하지 않는 사람(언팔로워)**을 가장 안전하고 빠르게 찾을 수 있는 웹사이트 서비스입니다. 
        """)
        
        st.divider()
        
        st.markdown("""
        ### QnA
        #### 1. 제 개인정보 유출 위험은 없나요?\n
            이 웹사이트는 외부 서버와 전혀 연결되어 있지 않으며,
            모든 분석은 현재 켜져 있는 웹사이트(내 컴퓨터/스마트폰) 안에서만 이루어집니다. \n
            따라서 창을 닫는 즉시 여러분의 데이터는 모두 삭제되기 때문에 개인정보 유출 위험은 없습니다.

        #### 2. 계정 밴(Ban)의 위험은 없나요?\n
            시중의 언팔로우 확인 앱들은 인스타그램 아이디와 비밀번호를 요구하거나
            불법 봇(Bot)을 이용하기 때문에 계정이 해킹당하거나 정지(섀도우 밴)될 위험이 매우 높습니다.\n
            그러나 Isntsta는 인스타그램 공식 백업 데이터만 활용하므로 계정에 아무런 영향을 주지 않습니다.
          
        #### 3. 언팔로워 중에서 대형 크리에이터 등을 걸러낼 수 있는 기능은 없나요?\n
            데이터 분석, 크롤링, API 등의 방법을 고안해봤으나 이들 모두 기술적으로 구현 불가능하거나
            Instagram 규정 위반이기 때문에 해당 기능은 기술적으로 만들기 어렵습니다.\n
            혹시 앞선 방법 말고 구현 가능한 분이 계시다면 저에게 연락해주세요.
        """)

    def render_instructions(self):
        st.subheader("💡 인스타그램 데이터 다운로드 및 이용 방법")
        
        step = st.session_state['instruction_step']
        total_steps = 4

        st.markdown(f"<div style='text-align: center; color: #833ab4; font-weight: bold; margin-bottom: 10px;'>{step} / {total_steps} 단계</div>", unsafe_allow_html=True)

        if step == 1:
            st.markdown('<h4 class="insta-subtitle">1단계: Instagram에 내 데이터 다운로드 요청하기</h4>', unsafe_allow_html=True)
        elif step == 2:
            st.markdown('<h4 class="insta-subtitle">2단계: 백업 파일 다운로드</h4>', unsafe_allow_html=True)
        elif step == 3:
            st.markdown('<h4 class="insta-subtitle">3단계: 분석기에 파일 업로드하기</h4>', unsafe_allow_html=True)
        elif step == 4:
            st.markdown('<h4 class="insta-subtitle">4단계: 맞팔 분석 시작</h4>', unsafe_allow_html=True)

        st.write("")

        try:
            col_l, col_img, col_r = st.columns([1, 5, 1], vertical_alignment="center")
        except TypeError:
            col_l, col_img, col_r = st.columns([1, 5, 1])

        with col_l:
            if step > 1:
                st.button("◀", key="prev_btn", on_click=self.prev_step, use_container_width=True)

        with col_img:
            if step == 1:
                if os.path.exists("step1.jpg"): st.image("step1.jpg", use_container_width=True)
                else: st.info("📷 (1단계 이미지 준비 중)")
            elif step == 2:
                if os.path.exists("step2.jpg"): st.image("step2.jpg", use_container_width=True)
                else: st.info("📷 (2단계 이미지 준비 중)")
            elif step == 3:
                if os.path.exists("step3.jpeg"): st.image("step3.jpeg", use_container_width=True)
                else: st.info("📷 (3단계 이미지 준비 중)")
            elif step == 4:
                st.markdown("<h1 style='text-align: center; font-size: 5rem; margin: 20px 0;'>🎉</h1>", unsafe_allow_html=True)

        with col_r:
            if step < total_steps:
                st.button("▶", key="next_btn", on_click=self.next_step, use_container_width=True)

        st.divider()

        if step == 1:
            st.markdown("""
            <div style="color: #C13584; font-size: 1rem;">
                <ol>
                    <li>Instagram 앱에서 <strong style="color: #FCAF45; text-shadow: 0px 0px 1px rgba(0,0,0,0.2);">메뉴(줄 3개)</strong> ➔ <strong style="color: #FCAF45; text-shadow: 0px 0px 1px rgba(0,0,0,0.2);">계정 센터</strong> ➔ <strong style="color: #FCAF45; text-shadow: 0px 0px 1px rgba(0,0,0,0.2);">내 정보 및 권한</strong>으로 이동합니다.</li>
                    <li><strong style="color: #FCAF45; text-shadow: 0px 0px 1px rgba(0,0,0,0.2);">내 정보 내보내기</strong> ➔ <strong style="color: #FCAF45; text-shadow: 0px 0px 1px rgba(0,0,0,0.2);">내보내기 만들기</strong> ➔ <strong style="color: #FCAF45; text-shadow: 0px 0px 1px rgba(0,0,0,0.2);">Instagram</strong> ➔ <strong style="color: #FCAF45; text-shadow: 0px 0px 1px rgba(0,0,0,0.2);">기기로 내보내기</strong>를 순서대로 선택합니다.</li>
                </ol>
                <hr style="margin: 10px 0px; border-color: #f0f2f6;">
                <p style="margin-bottom: 5px;"><strong style="color: #FCAF45; text-shadow: 0px 0px 1px rgba(0,0,0,0.2);">🚨 중요 설정 안내</strong></p>
                <ul>
                    <li><strong style="color: #FCAF45; text-shadow: 0px 0px 1px rgba(0,0,0,0.2);">정보 맞춤 설정</strong> 단계에서 반드시 <strong style="color: #FCAF45; text-shadow: 0px 0px 1px rgba(0,0,0,0.2);">팔로워 및 팔로잉</strong> 정보가 체크되어 있어야 합니다.</li>
                    <li><strong style="color: #FCAF45; text-shadow: 0px 0px 1px rgba(0,0,0,0.2);">기간</strong> 설정 시 <strong style="color: #FCAF45; text-shadow: 0px 0px 1px rgba(0,0,0,0.2);">전체 기간</strong>을 선택하셔야 누락 없는 정확한 분석이 가능합니다.</li>
                </ul>
                <hr style="margin: 10px 0px; border-color: #f0f2f6;">
                <ol start="3">
                    <li><strong style="color: #FCAF45; text-shadow: 0px 0px 1px rgba(0,0,0,0.2);">내보내기 시작</strong>을 누릅니다.</li>
                </ol>
            </div>
            """, unsafe_allow_html=True)

        elif step == 2:
            st.markdown('<ul style="color: #C13584;"><li>요청 후 대략 10분에서 1시간 이내에 인스타그램으로부터 이메일 알림이 도착합니다. 이메일 본문의 링크를 클릭하여 .zip 파일을 다운로드해 주세요.</li></ul>', unsafe_allow_html=True)

        elif step == 3:
            st.markdown('<ul style="color: #C13584;"><li>상단의 <strong style="color: #FCAF45; text-shadow: 0px 0px 1px rgba(0,0,0,0.2);">ZIP 파일 업로드</strong> 탭을 선택한 뒤, 다운로드한 .zip 파일을 <strong style="color: #FCAF45; text-shadow: 0px 0px 1px rgba(0,0,0,0.2);">압축을 풀지 말고 파일 업로드 박스에 그대로</strong> 끌어다 놓습니다.</li></ul>', unsafe_allow_html=True)

        elif step == 4:
            st.markdown('<ul style="color: #C13584;"><li>파일이 정상적으로 올라가면 <strong style="color: #FCAF45; text-shadow: 0px 0px 1px rgba(0,0,0,0.2);">📦 ZIP 파일 업로드</strong> 탭으로 이동하여 하단에 생성된 <strong style="color: #FCAF45; text-shadow: 0px 0px 1px rgba(0,0,0,0.2);">맞팔 분석 시작</strong> 버튼을 클릭하고 결과를 확인합니다.</li></ul>', unsafe_allow_html=True)

    def render_upload_section(self):
        st.info("💡 다운로드한 .zip 파일을 압축 해제하지 말고 그대로 업로드해 주세요. (HTML 및 JSON 형식 모두 지원)")
        zip_file = st.file_uploader("ZIP 파일 업로드 (.zip)", type=['zip'], key='zip_upload', on_change=self.reset_analysis)
        
        if zip_file is not None and not st.session_state['data_loaded']:
            try:
                with zipfile.ZipFile(zip_file) as z:
                    followers_path = next((f for f in z.namelist() if f.split('/')[-1].startswith('followers') and f.endswith(('.html', '.json'))), None)
                    following_path = next((f for f in z.namelist() if f.split('/')[-1].startswith('following') and f.endswith(('.html', '.json'))), None)
                            
                    if followers_path and following_path:
                        followers_ext = followers_path.split('.')[-1]
                        following_ext = following_path.split('.')[-1]
                        
                        with st.spinner("데이터를 추출하고 있습니다. 잠시만 기다려 주세요..."):
                            st.session_state['followers_df'] = InstagramDataParser.parse(z.read(followers_path), followers_ext)
                            st.session_state['following_df'] = InstagramDataParser.parse(z.read(following_path), following_ext)
                        st.session_state['data_loaded'] = True
                        st.success("데이터 추출이 완료되었습니다. 아래에서 분석을 진행해 주세요.")
                    else:
                        st.error("ZIP 파일 내부에 팔로워 또는 팔로잉 데이터 파일이 존재하지 않습니다. 올바른 백업 파일인지 확인해 주세요.")
            except Exception as e:
                st.error(f"ZIP 파일을 읽는 중 오류가 발생했습니다: {e}")

    def render_analysis_section(self):
        if st.session_state['data_loaded']:
            st.divider()

            deactivated_input = st.text_area(
                "🚫 분석에서 제외할 계정 (비활성화 계정, 유명인, 브랜드 계정 등) - 선택사항", 
                placeholder="쉼표 또는 줄바꿈으로 구분하여 입력해 주세요.\n예: gov_korea, k_yseok.07"
            )

            if st.button("🚀 맞팔 분석 시작", use_container_width=True):
                deactivated_list = [x.strip() for x in deactivated_input.replace(',', '\n').split('\n') if x.strip()]
                
                analyzer = InstagramAnalyzer(
                    st.session_state['followers_df'],
                    st.session_state['following_df'],
                    deactivated_list
                )
                
                st.session_state['analysis_result'] = analyzer.analyze()
                st.session_state['analyzed'] = True

            if st.session_state['analyzed']:
                self.render_results(st.session_state['analysis_result'])

    def render_results(self, result: dict):
        st.subheader("📊 분석 결과")
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("총 팔로워", f"{result['total_followers']}명")
        col_b.metric("데이터상 총 팔로잉", f"{result['total_following']}명")
        col_c.metric("나를 맞팔하지 않는 사람", f"{result['unfollowers_count']}명", delta="-언팔로워", delta_color="inverse")
        
        st.warning("""
        **⚠️ 분석 결과 확인 전 주의사항**
        * 상대방이 계정을 일시 **비활성화**, **삭제** 또는 **정지**한 경우 실제 인스타그램 앱에 표시되는 수치와 다를 수 있습니다.
        * 본 분석 결과는 참고용으로 활용하고 정확한 내역은 인스타그램 앱에서 **직접 교차 확인하시는 것을 권장**합니다.
        """)
        
        st.divider()
        st.subheader("👀 나를 맞팔하지 않는 계정 목록")
        st.caption("사용자 이름을 클릭하여 해당 사용자의 프로필을 조회할 수 있습니다.\n열 제목을 클릭하여 정렬 순서를 바꿀 수 있습니다.")
        
        result_df = result['result_df']
        
        if not result_df.empty:
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

    def render_developer_section(self):
        st.subheader("Developer")
        
        st.markdown("""
        **윤슥** ( kyunseok@postech.ac.kr )

        Other websites:
        - [Isntsta](https://isntsta.streamlit.app/)
        - [Kakaotalk Analyzer](https://kakaodog.streamlit.app/)
        - [Guitarhana](https://guitarhana.streamlit.app/)
        \n(위 웹사이트가 접속이 안될 경우 이는 일시적으로 웹사이트 서버가 중단되었기 때문입니다.)
        """)
        
        st.divider()
        st.info("""### 데이터 보안 및 투명성 명시 ###
        \n본 웹사이트는 사용자의 데이터를 외부 서버로 전송하거나 저장하지 않으며, 웹사이트의 로컬 메모리 내에서만 안전하게 동작합니다.""")

if __name__ == "__main__":
    app = InstagramAppUI()
    app.run()
