from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


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
        ('claimed', 'Claimed'),
    )
    
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField(blank=True, null=True)
    date_requested = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.user.username} - {self.item.title} ({self.status})"


class UserBan(models.Model):
    """Model to track user bans and penalties"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_ban')
    is_banned = models.BooleanField(default=False)
    ban_reason = models.TextField(blank=True, null=True)
    date_banned = models.DateTimeField(auto_now_add=True)
    banned_until = models.DateTimeField(null=True, blank=True)  # null = permanent ban
    
    def is_currently_banned(self):
        """Check if user is currently banned"""
        if not self.is_banned:
            return False
        if self.banned_until is None:
            # Permanent ban
            return True
        # Check if temporary ban is still active
        return timezone.now() < self.banned_until
    
    def __str__(self):
        ban_type = "Permanent" if self.banned_until is None else f"Until {self.banned_until.strftime('%Y-%m-%d %H:%M')}"
        return f"{self.user.username} - Banned ({ban_type})"