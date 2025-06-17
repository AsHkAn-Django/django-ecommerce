import pandas as pd
from surprise import Dataset, Reader, SVD
from myApp.models import Rating


def get_top_n_recommendations(user_id, n=5):
    # 1. Fetch data from Django model
    ratings_qs = Rating.objects.all().values('user_id', 'book_id', 'rate')
    ratings_df = pd.DataFrame.from_records(ratings_qs)

    # 2. Check if DataFrame is valid
    required_columns = {'user_id', 'book_id', 'rate'}
    if ratings_df.empty or not required_columns.issubset(set(ratings_df.columns)):
        return []

    # 3. Define the data format for Surprise
    reader = Reader(rating_scale=(1, 5))
    data = Dataset.load_from_df(ratings_df[['user_id', 'book_id', 'rate']], reader)

    # 4. Train the model
    trainset = data.build_full_trainset()
    model = SVD()
    model.fit(trainset)

    # 5. Get all book IDs
    all_book_ids = ratings_df['book_id'].unique()

    # 6. Get books this user already rated
    rated_books = ratings_df[ratings_df['user_id'] == user_id]['book_id'].tolist()

    # 7. Filter out already rated books
    books_to_predict = [bid for bid in all_book_ids if bid not in rated_books]

    # 8. Predict ratings for the unseen books
    predictions = [model.predict(user_id, bid) for bid in books_to_predict]

    # 9. Sort and return top n recommendations
    top_predictions = sorted(predictions, key=lambda x: x.est, reverse=True)[:n]
    top_book_ids = [int(pred.iid) for pred in top_predictions]

    return top_book_ids
