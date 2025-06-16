import pandas as pd
from surprise import Dataset, Reader, SVD

from myApp.models import Rating

# 1. Fetch data from Django model
ratings_qs = Rating.objects.all().values('user_id', 'book_id', 'rate')

# 2. Convert to a DataFrame
ratings_df = pd.DataFrame.from_records(ratings_qs)

# 3. Define the data format for Surprise
reader = Reader(rating_scale=(1, 5))  # our rating goes from 1.0 to 5.0
data = Dataset.load_from_df(ratings_df[['user_id', 'book_id', 'rate']], reader)

# 4. Train the model
trainset = data.build_full_trainset()  # use all data to train
model = SVD()  # Singular Value Decomposition (a popular CF algorithm)
model.fit(trainset)

# 5. Make recommendation for a specific user (change the ID below)
def get_top_n_recommendations(user_id, n=5):
    # Get all book IDs
    all_book_ids = ratings_df['book_id'].unique()

    # Get books this user already rated
    rated_books = ratings_df[ratings_df['user_id'] == user_id]['book_id'].tolist()

    # Filter out books the user has already rated
    books_to_predict = [bid for bid in all_book_ids if bid not in rated_books]

    # Predict ratings for the unseen books
    predictions = [model.predict(user_id, bid) for bid in books_to_predict]

    # Sort predictions by estimated rating
    top_predictions = sorted(predictions, key=lambda x: x.est, reverse=True)[:n]

    # Get book IDs from the top predictions
    top_book_ids = [int(pred.iid) for pred in top_predictions]

    return top_book_ids
