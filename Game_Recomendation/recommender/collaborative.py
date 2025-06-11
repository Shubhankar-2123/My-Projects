# from surprise import Dataset, Reader, KNNBasic
# from surprise.model_selection import train_test_split
# import pandas as pd

# class CollaborativeRecommender:
#     def __init__(self, ratings_data):
#         self.ratings = ratings_data
#         self.reader = Reader(rating_scale=(1, 5))
#         self.model = None
#         self._train_model()
    
#     def _train_model(self):
#         # Load data into Surprise dataset
#         data = Dataset.load_from_df(self.ratings[['user_id', 'game_id', 'rating']], self.reader)
        
#         # Build trainset
#         trainset = data.build_full_trainset()
        
#         # Use user-based KNN
#         sim_options = {
#             'name': 'cosine',
#             'user_based': True
#         }
        
#         self.model = KNNBasic(sim_options=sim_options)
#         self.model.fit(trainset)
    
#     def recommend(self, user_id, n=5):
#         # Get list of all game IDs
#         all_game_ids = self.ratings['game_id'].unique()
        
#         # Get games the user has already rated
#         rated_games = self.ratings[self.ratings['user_id'] == user_id]['game_id'].tolist()
        
#         # Predict ratings for unrated games
#         predictions = []
#         for game_id in all_game_ids:
#             if game_id not in rated_games:
#                 pred = self.model.predict(user_id, game_id)
#                 predictions.append((game_id, pred.est))
        
#         # Sort by predicted rating
#         predictions.sort(key=lambda x: x[1], reverse=True)
        
#         return predictions[:n]
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

class CollaborativeRecommender:
    def __init__(self, ratings_data, games_data):
        self.ratings = ratings_data
        self.games = games_data
        self.user_item_matrix = self._create_matrix()
        self.user_similarity = cosine_similarity(self.user_item_matrix)

    def _create_matrix(self):
        matrix = self.ratings.pivot_table(
            index='user_id',
            columns='game_url',
            values='rating',
            fill_value=0
        )
        user_means = matrix.mean(axis=1)
        return matrix.sub(user_means, axis=0)

    def recommend(self, user_id, n=5):
        try:
            user_idx = self.user_item_matrix.index.get_loc(user_id)
            sim_scores = list(enumerate(self.user_similarity[user_idx]))
            sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:n+1]
            
            recommendations = pd.Series(0, index=self.user_item_matrix.columns)
            for similar_user_idx, similarity in sim_scores:
                recommendations += self.user_item_matrix.iloc[similar_user_idx] * similarity
            
            played_games = self.ratings[self.ratings['user_id'] == user_id]['game_url']
            recs = recommendations[~recommendations.index.isin(played_games)]
            top_urls = recs.sort_values(ascending=False).head(n).index
            
            return self.games[self.games['URL'].isin(top_urls)]
        except KeyError:
            return pd.DataFrame()