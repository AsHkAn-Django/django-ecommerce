from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
from django.conf import settings
from decimal import Decimal
from django.utils.text import slugify
import os



def book_image_upload_path(instance, filename):
    title_slug = slugify(instance.title)
    return os.path.join('uploads', title_slug, filename)



class Book(models.Model):
    title = models.CharField(max_length=264)
    author = models.CharField(max_length=264)
    price = models.DecimalField(max_digits=6, decimal_places=2,
                                validators=[MinValueValidator(0)])
    stock = models.IntegerField(validators=[MinValueValidator(0)], default=0)
    image = models.ImageField(upload_to=book_image_upload_path, blank=True)
    description = models.CharField(max_length=264, null=True, blank=True)

    def get_absolute_url(self):
        return reverse('myApp:home')

    def stock_lower_than10(self):
        if self.stock < 10:
            return True
        return False

    def get_average_rating(self):
        ratings = self.book_ratings.all()
        if not ratings:
            return Decimal('0.0')
        else:
            total = sum(rating.rate for rating in ratings)
        return Decimal(round(total / len(ratings), 1))

    def get_rates_number(self):
        return len(self.book_ratings.all())

    def __str__(self):
        return self.title



class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='user_favorites')
    book = models.ForeignKey(Book, on_delete=models.CASCADE,
                             related_name='book_favorites')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} added {self.book.title}"


class Rating(models.Model):
    rate = models.DecimalField(max_digits=2, decimal_places=1, validators=(
        MaxValueValidator(5.0), MinValueValidator(1.0)))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='user_ratings')
    book = models.ForeignKey(Book, on_delete=models.CASCADE,
                             related_name='book_ratings')
    review = models.CharField(max_length=250, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Each user have one rating per book
        constraints = [
            models.UniqueConstraint(fields=['book', 'user'],
                                    name='unnique_book_user_rating')
        ]

    def __str__(self):
        return f"{self.user.username} rated {self.rate} to {self.book.title}"