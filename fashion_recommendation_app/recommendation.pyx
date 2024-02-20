# recommendation.pyx
import numpy as np
cimport numpy as np

def recommend(dict user_item_matrix, int user_id, int top_n=5):
    cdef dict similarities = {}
    cdef np.ndarray[np.float64_t, ndim=1] target_user_ratings
    cdef int other_user_id
    cdef np.ndarray[np.float64_t, ndim=1] other_user_ratings
    cdef np.float64_t similarity_scores

    # Get ratings for the target user
    target_user_ratings = np.array(user_item_matrix[user_id], dtype=np.float64)

    # Find the maximum length of ratings among all users
    max_ratings_length = max(len(ratings) for ratings in user_item_matrix.values())

    # Iterate over other users
    for other_user_id, other_user_ratings in user_item_matrix.items():
        if other_user_id != user_id:
            # Convert ratings to numpy arrays
            other_user_ratings = np.array(other_user_ratings, dtype=np.float64)
            # Pad vectors with zeros to match the maximum length
            target_user_ratings_padded = np.pad(target_user_ratings, (0, max_ratings_length - len(target_user_ratings)), mode='constant')
            other_user_ratings_padded = np.pad(other_user_ratings, (0, max_ratings_length - len(other_user_ratings)), mode='constant')
            # Calculate similarity score
            similarity_scores = np.dot(target_user_ratings_padded, other_user_ratings_padded) / (np.linalg.norm(target_user_ratings_padded) * np.linalg.norm(other_user_ratings_padded))
            # Store similarity score
            similarities[other_user_id] = similarity_scores

    # Sort similarities
    sorted_similarities = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
    # Get top similar users
    top_similar_users = [user_id for user_id, _ in sorted_similarities[:top_n]]
    
    # Initialize recommendations list
    recommendations = []

    # Iterate over top similar users
    for other_user_id in top_similar_users:
        other_user_ratings = user_item_matrix[other_user_id]
        # Check if the user has rated items not rated by the target user
        for i, rating in enumerate(other_user_ratings):
            if rating == 1 and user_item_matrix[user_id][i] == 0:
                recommendations.append(i)
                if len(recommendations) == top_n:
                    return recommendations

    # Return recommendations if found, otherwise return an empty list
    return recommendations
