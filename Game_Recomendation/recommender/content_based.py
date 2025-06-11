import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

class ContentBasedRecommender:
    def __init__(self, games_data):
        self.games = games_data.fillna('')
        self.tfidf = TfidfVectorizer(stop_words='english')
        self.cosine_sim = None
        self._prepare_model()

    def _prepare_model(self):
        self.games['combined_features'] = (
            self.games['Primary Genre'] + ' ' +
            self.games['Genres'] + ' ' +
            self.games['Description'] + ' ' +
            self.games['Developer']
        )
        tfidf_matrix = self.tfidf.fit_transform(self.games['combined_features'])
        self.cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)

    def recommend(self, game_url, n=5):
        try:
            idx = self.games.index[self.games['URL'] == game_url].tolist()[0]
            sim_scores = list(enumerate(self.cosine_sim[idx]))
            sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
            game_indices = [i[0] for i in sim_scores[1:n+1]]
            return self.games.iloc[game_indices]
        except IndexError:
            return pd.DataFrame()