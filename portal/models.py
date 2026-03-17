from django.db import models
from django.contrib.auth.models import User


class Item(models.Model):
    ITEM_TYPES = (
        ('Lost', 'Lost'),
        ('Found', 'Found'),
    )

    title = models.CharField(max_length=100)
    description = models.TextField()
    location = models.CharField(max_length=100)
    item_type = models.CharField(max_length=10, choices=ITEM_TYPES)
    image = models.ImageField(upload_to='items/', null=True, blank=True)
    date_posted = models.DateTimeField(auto_now_add=True)
    is_claimed = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class ClaimRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField(blank=True, null=True)
    date_requested = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.user.username} - {self.item.title} ({self.status})"