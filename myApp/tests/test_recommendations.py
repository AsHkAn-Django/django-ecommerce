import pytest
from myApp.models import Rating
from myApp.recommend import get_top_n_recommendations


@pytest.mark.django_db
def test_recommendation_empty_db_returns_empty_list():
    """
    If there are no ratings in the system,
    the function should fail gracefully (return empty list)
    instead of crashing Pandas/Surprise.
    """
    user_id = 1
    recommendations = get_top_n_recommendations(user_id)
    assert recommendations == []


@pytest.mark.django_db
def test_recommendation_returns_unseen_books(create_user, create_book):
    """
    Test that the system recommends books the user hasn't seen yet.
    """
    me = create_user(email="me@test.com", password="pw")

    book_read = create_book(title="Read Book")
    book_unread_1 = create_book(title="Unread 1")
    book_unread_2 = create_book(title="Unread 2")

    # Create 'Other' users to generate collaborative data
    other = create_user(email="other@test.com", password="pw")

    # I read book_read (5 stars)
    Rating.objects.create(user=me, book=book_read, rate=5.0)

    # Other guy read ALL books (so the system knows they exist)
    Rating.objects.create(user=other, book=book_read, rate=5.0)
    Rating.objects.create(user=other, book=book_unread_1, rate=4.0)
    Rating.objects.create(user=other, book=book_unread_2, rate=5.0)

    # Get recommendations for ME
    recs = get_top_n_recommendations(me.id, n=5)

    # Should NOT contain the book I already read
    assert book_read.id not in recs

    # Should contain the unread books (because 'other' rated them highly)
    assert len(recs) > 0
    assert book_unread_1.id in recs or book_unread_2.id in recs


@pytest.mark.django_db
def test_recommendation_limit_n(create_user, create_book):
    """
    Test that the 'n' parameter limits the number of results.
    """
    me = create_user(email="limit@test.com", password="pw")
    other = create_user(email="other@test.com", password="pw")

    # Create 10 books
    books = [create_book(title=f"Book {i}") for i in range(10)]

    # Other user rates ALL of them so they are candidates
    for book in books:
        Rating.objects.create(user=other, book=book, rate=5.0)

    # I rate nothing (Cold Start)

    # Ask for top 3
    recs = get_top_n_recommendations(me.id, n=3)

    # Should get exactly 3 items max
    assert len(recs) <= 3
