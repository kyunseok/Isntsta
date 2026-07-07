import pandas as pd

class InstagramAnalyzer:
    """팔로워/팔로잉 데이터를 비교하고 분석하는 비즈니스 로직"""
    
    def __init__(self, followers_df: pd.DataFrame, following_df: pd.DataFrame, deactivated_list: list):
        self.followers_df = followers_df
        self.following_df = following_df
        self.deactivated_set = set(deactivated_list)

    def analyze(self) -> dict:
        followers_set = set(self.followers_df['Username'])
        following_set = set(self.following_df['Username'])
        
        filtered_following = following_set - self.deactivated_set
        filtered_followers = followers_set - self.deactivated_set
        
        unfollowers = filtered_following - filtered_followers

        # 필터링
        result_df = self.following_df[self.following_df['Username'].isin(unfollowers)].copy()
        result_df["Profile_URL"] = result_df["Username"].apply(lambda x: f"https://www.instagram.com/{x}/")
        
        return {
            'total_followers': len(filtered_followers),
            'total_following': len(filtered_following),
            'unfollowers_count': len(unfollowers),
            'result_df': result_df
        }
