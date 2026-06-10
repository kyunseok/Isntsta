import streamlit as st
from bs4 import BeautifulSoup
import pandas as pd

class InstagramHTMLParser:
    """HTML 데이터를 파싱하여 데이터프레임으로 변환하는 책임을 가집니다."""
    
    @staticmethod
    @st.cache_data
    def parse(html_content: bytes) -> pd.DataFrame:
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