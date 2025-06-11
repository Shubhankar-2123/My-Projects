import pandas as pd

class HybridRecommender:
    def __init__(self, games_data, ratings_data):
        self.games = games_data
        self.ratings = ratings_data
        from .content_based import ContentBasedRecommender
        from .collaborative import CollaborativeRecommender
        self.cb = ContentBasedRecommender(games_data)
        self.cf = CollaborativeRecommender(ratings_data, games_data)

    def recommend(self, user_id=None, game_url=None, n=5):
        if user_id is None and game_url is None:
            return self.games.sort_values('User Rating Count', ascending=False).head(n)
        
        if game_url is not None:
            return self.cb.recommend(game_url, n)
        
        if user_id is not None:
            cf_recs = self.cf.recommend(user_id, n)
            if not cf_recs.empty:
                return cf_recs
            else:
                top_game = self.ratings[self.ratings['user_id'] == user_id]\
                          .sort_values('rating', ascending=False)\
                          .iloc[0]['game_url']
                return self.cb.recommend(top_game, n)