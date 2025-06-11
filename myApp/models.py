from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.urls import reverse



class Book(models.Model):
    title = models.CharField(max_length=264)
    author = models.CharField(max_length=264)
    price = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    stock = models.IntegerField(validators=[MinValueValidator(0)]) 
    
    def get_absolute_url(self):
        return reverse('myApp:home')

    def __str__(self):
        return self.title
    
    def stock_lower_than10(self):
        if self.stock < 10:
            return True
        return False
        
        
class CartItem(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='cart_items')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchased_items')
    add_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.book.title
 