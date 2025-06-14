# import pandas as pd
# import numpy as np
# from sklearn.metrics.pairwise import cosine_similarity
# from sklearn.feature_extraction.text import TfidfVectorizer
# from collections import defaultdict
# import sqlite3

# class GameRecommender:
#     def __init__(self, data_path):
#         self.games_df = pd.read_csv(data_path)
#         self.game_id_to_idx = {game_id: idx for idx, game_id in enumerate(self.games_df['URL'])}
#         self.prepare_data()
#         self.build_similarity_matrix()
        
#     def prepare_data(self):
#         # Clean and prepare data
#         self.games_df = self.games_df.drop_duplicates(subset=['URL'])
#         self.games_df['Description'] = self.games_df['Description'].fillna('')
#         self.games_df['Primary Genre'] = self.games_df['Primary Genre'].fillna('Unknown')
#         self.games_df['Genres'] = self.games_df['Genres'].fillna('Unknown')
        
#         # Create combined features for content-based filtering
#         self.games_df['combined_features'] = (
#             self.games_df['Primary Genre'] + ' ' + 
#             self.games_df['Genres'] + ' ' + 
#             self.games_df['Description']
#         )
        
#     def build_similarity_matrix(self):
#         # TF-IDF Vectorizer
#         tfidf = TfidfVectorizer(stop_words='english', max_features=5000)
#         tfidf_matrix = tfidf.fit_transform(self.games_df['combined_features'])
        
#         # Compute cosine similarity
#         self.cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
        
#     def get_recommendations(self, user_id, top_n=10):
#         # Check if user exists and has interactions
#         conn = sqlite3.connect('data/recommendations.db')
#         c = conn.cursor()
        
#         # Get user's rated games and ratings
#         c.execute('''SELECT game_id, value FROM interactions 
#                      WHERE user_id = ? AND interaction_type = 'rating' 
#                      ORDER BY timestamp DESC''', (user_id,))
#         user_ratings = c.fetchall()
#         conn.close()
        
#         if not user_ratings:
#             return self.get_popular_games(top_n)
        
#         # Create user profile based on ratings
#         user_profile = np.zeros(len(self.games_df))
#         for game_id, rating in user_ratings:
#             if game_id in self.game_id_to_idx:
#                 idx = self.game_id_to_idx[game_id]
#                 user_profile += self.cosine_sim[idx] * rating
        
#         # Normalize
#         user_profile /= len(user_ratings)
        
#         # Get top similar games
#         sim_scores = list(enumerate(user_profile))
#         sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        
#         # Filter out games user has already rated
#         rated_game_ids = {game_id for game_id, _ in user_ratings}
#         recommendations = []
#         for idx, score in sim_scores:
#             game_id = self.games_df.iloc[idx]['URL']
#             if game_id not in rated_game_ids:
#                 recommendations.append((idx, score))
#             if len(recommendations) >= top_n:
#                 break
                
#         # Get game details for recommendations
#         recommended_games = self.games_df.iloc[[idx for idx, _ in recommendations]]
#         return recommended_games.to_dict('records')
    
#     def get_popular_games(self, top_n=10):
#         # Get games with highest rating count and good average rating
#         popular = self.games_df[
#             (self.games_df['User Rating Count'] > 10) & 
#             (self.games_df['Average User Rating'] >= 3.5)
#         ].sort_values(
#             by=['User Rating Count', 'Average User Rating'],
#             ascending=False
#         ).head(top_n)
        
#         return popular.to_dict('records')
    
#     def get_game_details(self, game_id):
#         game = self.games_df[self.games_df['URL'] == game_id].iloc[0]

#         return game.to_dict()

import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import defaultdict
import sqlite3
import os
from scipy.sparse import csr_matrix

class GameRecommender:
    def __init__(self, data_path, max_games=5000):
        """Initialize with memory limits"""
        try:
            # Load game data with memory optimization
            self.games_df = pd.read_csv(data_path, nrows=max_games)
            
            # Validate required columns
            required_columns = {
                'URL', 'Name', 'Icon URL', 'Average User Rating',
                'User Rating Count', 'Description', 'Developer',
                'Primary Genre', 'Genres'
            }
            missing_cols = required_columns - set(self.games_df.columns)
            if missing_cols:
                raise ValueError(f"Missing columns: {missing_cols}")
            
            self._create_mappings()
            self.prepare_data()
            self.build_similarity_matrix()
            
        except Exception as e:
            raise RuntimeError(f"Initialization failed: {str(e)}")

    def _create_mappings(self):
        """Create memory-efficient mappings"""
        self.games_df = self.games_df.drop_duplicates(subset=['URL'])
        self.game_id_to_idx = {
            game_id: idx for idx, game_id in enumerate(self.games_df['URL'])
        }
        self.idx_to_game_id = {
            idx: game_id for game_id, idx in self.game_id_to_idx.items()
        }

    def prepare_data(self):
        """Clean data with memory efficiency"""
        text_cols = ['Description', 'Primary Genre', 'Genres', 'Developer']
        for col in text_cols:
            if col in self.games_df.columns:
                self.games_df[col] = self.games_df[col].fillna('').astype(str)
        
        self.games_df['combined_features'] = (
            self.games_df['Primary Genre'] + ' ' + 
            self.games_df['Genres'] + ' ' + 
            self.games_df['Description'].str[:500] + ' ' +  # Limit description size
            self.games_df['Developer']
        )

    def build_similarity_matrix(self):
        """Build memory-efficient similarity matrix"""
        tfidf = TfidfVectorizer(
            stop_words='english',
            max_features=2000,  # Reduced features
            ngram_range=(1, 1)  # Only unigrams
        )
        
        # Use sparse matrices
        tfidf_matrix = tfidf.fit_transform(self.games_df['combined_features'])
        
        # Calculate similarity in batches
        self.similarity_batches = []
        batch_size = 1000
        for i in range(0, tfidf_matrix.shape[0], batch_size):
            batch = tfidf_matrix[i:i+batch_size]
            sim_batch = cosine_similarity(batch, tfidf_matrix)
            self.similarity_batches.append(csr_matrix(sim_batch))  # Keep sparse

    def _get_similarity_row(self, idx):
        """Get similarity row from batches"""
        batch_idx = idx // 1000
        row_in_batch = idx % 1000
        return self.similarity_batches[batch_idx].getrow(row_in_batch).toarray()[0]

    def get_recommendations(self, user_id, top_n=10):
        """Memory-efficient recommendations"""
        try:
            # Get user ratings from database
            conn = sqlite3.connect('data/recommendations.db')
            c = conn.cursor()
            c.execute('''SELECT game_url, value FROM interactions 
                         WHERE user_id = ? AND interaction_type = 'rating' 
                         ORDER BY timestamp DESC''', (user_id,))
            user_ratings = c.fetchall()
            conn.close()
            
            if not user_ratings:
                return self.get_popular_games(top_n)
            
            # Build user profile using batches
            user_profile = np.zeros(len(self.games_df))
            valid_ratings = 0
            
            for game_url, rating in user_ratings:
                if game_url in self.game_id_to_idx:
                    idx = self.game_id_to_idx[game_url]
                    user_profile += self._get_similarity_row(idx) * rating
                    valid_ratings += 1
            
            if valid_ratings == 0:
                return self.get_popular_games(top_n)
                
            user_profile /= valid_ratings
            
            # Get top recommendations without full matrix
            rated_game_urls = {url for url, _ in user_ratings}
            recommendations = []
            
            for idx in np.argsort(user_profile)[::-1]:  # Sort descending
                game_url = self.idx_to_game_id[idx]
                if game_url not in rated_game_urls:
                    recommendations.append(idx)
                if len(recommendations) >= top_n:
                    break
                    
            return self.games_df.iloc[recommendations].to_dict('records')
            
        except Exception as e:
            print(f"Recommendation error: {e}")
            return self.get_popular_games(top_n)

    def get_popular_games(self, top_n=10):
        """Get popular games as fallback"""
        try:
            popular = self.games_df[
                (self.games_df['User Rating Count'] > 10) & 
                (self.games_df['Average User Rating'] >= 3.5)
            ].sort_values(
                by=['User Rating Count', 'Average User Rating'],
                ascending=False
            ).head(top_n)
            
            return popular.to_dict('records')
        except:
            # Fallback if any columns are missing
            return self.games_df.head(top_n).to_dict('records')

    def get_game_details(self, game_url):
        """Get details for a specific game"""
        try:
            game = self.games_df[self.games_df['URL'] == game_url].iloc[0]
            return game.to_dict()
        except:
            return None

    def get_game_by_name(self, game_name):
        """Lookup game by name (case insensitive)"""
        try:
            game = self.games_df[
                self.games_df['Name'].str.lower() == game_name.lower()
            ].iloc[0]
            return game.to_dict()
        except:
            return None
    # ... (keep existing get_popular_games, get_game_details methods) ...