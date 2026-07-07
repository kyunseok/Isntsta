from bs4 import BeautifulSoup
import pandas as pd
import json
from datetime import datetime

class InstagramDataParser:
    """HTML 및 JSON 데이터를 파싱하여 데이터프레임으로 변환"""
    
    @staticmethod
    def parse(file_content: bytes, file_type: str) -> pd.DataFrame:
        if file_type == 'json':
            return InstagramDataParser._parse_json(file_content)
        elif file_type == 'html':
            return InstagramDataParser._parse_html(file_content)
        else:
            raise ValueError("지원하지 않는 파일 형식입니다.")

    @staticmethod
    def _parse_html(html_content: bytes) -> pd.DataFrame:
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

    @staticmethod
    def _parse_json(json_content: bytes) -> pd.DataFrame:
        data = json.loads(json_content)
        records = []
        def extract_users(obj):
            if isinstance(obj, dict):
                if "string_list_data" in obj and len(obj["string_list_data"]) > 0:
                    item = obj["string_list_data"][0]
                    if "value" in item and "timestamp" in item:
                        username = item["value"]
                        ts = item["timestamp"]
                        
                        # 유닉스 타임스탬프를 한국어 날짜 형식으로 변환
                        dt = datetime.fromtimestamp(ts)
                        ampm = "오후" if dt.hour >= 12 else "오전"
                        display_hour = dt.hour - 12 if dt.hour > 12 else dt.hour
                        display_hour = 12 if display_hour == 0 else display_hour
                        
                        date_str = f"{dt.year}년 {dt.month}월 {dt.day}일 {ampm} {display_hour}시 {dt.minute}분"
                        parsed_date = pd.Timestamp(dt.year, dt.month, dt.day, dt.hour, dt.minute)
                        
                        records.append({
                            'Username': username,
                            'Date': date_str,
                            'Parsed_Date': parsed_date
                        })
                else:
                    for value in obj.values():
                        extract_users(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_users(item)
                    
        extract_users(data)
        return pd.DataFrame(records).drop_duplicates(subset=['Username'])
