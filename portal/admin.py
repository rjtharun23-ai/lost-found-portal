from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import Item, ClaimRequest, UserBan


class CustomUserAdmin(BaseUserAdmin):
    """Custom User Admin with email field visible and credential sending"""
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'first_name', 'last_name'),
        }),
    )
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_superuser', 'is_active')

    def save_model(self, request, obj, form, change):
        """Override save to send email with credentials when creating new user"""
        is_new_user = not change  # change=False means new user
        plain_password = None
        
        # If new user, capture plain password before it's hashed
        if is_new_user:
            # Try to get password from form
            try:
                if hasattr(form, 'cleaned_data'):
                    plain_password = form.cleaned_data.get('password1')
                else:
                    plain_password = form.data.get('password1')
            except Exception as e:
                print(f"Error getting password: {e}")
        
        # Save the user (this hashes the password)
        super().save_model(request, obj, form, change)
        
        # Send credentials email if new user with email and password
        if is_new_user and obj.email:
            if plain_password:
                email_sent = self.send_credentials_email(request, obj, plain_password)
                if email_sent:
                    messages.success(request, f"✓ User '{obj.username}' created successfully. Credentials email sent to {obj.email}")
                else:
                    messages.warning(request, f"User '{obj.username}' created, but email sending failed. Check console for details.")
            else:
                messages.warning(request, f"User '{obj.username}' created, but no password was set. Email not sent.")
        elif is_new_user:
            messages.info(request, f"User '{obj.username}' created. No email address provided, so credentials email was not sent.")
    
    def send_credentials_email(self, request, user, password):
        """Send welcome email with credentials"""
        if not user.email:
            print(f"✗ No email address for user {user.username}")
            return False
            
        subject = "Welcome to SLT Portal - Your Account Credentials"
        
        message = f"""Hello {user.first_name or user.username},

Your account has been created on the SLT Portal (Lost & Found System).

Here are your login credentials:

Username: {user.username}
Password: {password}
Email: {user.email}

Please log in at: http://localhost:8000/
(Update the URL to match your deployment)

Role: Student

Instructions:
1. Go to the login page
2. Enter your username and password
3. Select "Student" as your role
4. Click Login

If you have any issues logging in or need to change your password, please contact the administration.

Best regards,
SLT Portal Administration"""
        
        try:
            print(f"\n📧 Sending credentials email to {user.email}...")
            result = send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            print(f"✓ Email sent successfully to {user.email}")
            print(f"  Username: {user.username}")
            print(f"  Password: {password}")
            return True
        except Exception as e:
            print(f"✗ Error sending email to {user.email}: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


# Unregister the default User admin and register custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


class ItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'item_type', 'location', 'is_claimed', 'date_posted')
    list_filter = ('item_type', 'is_claimed', 'date_posted')
    search_fields = ('title', 'description', 'location')
    readonly_fields = ('date_posted',)


class ClaimRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'item', 'status', 'date_requested')
    list_filter = ('status', 'date_requested')
    search_fields = ('user__username', 'item__title')
    readonly_fields = ('date_requested',)
    
    fieldsets = (
        ('Claim Information', {
            'fields': ('item', 'user', 'date_requested')
        }),
        ('Message', {
            'fields': ('message',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('status',)
        }),
    )
    
    def has_add_permission(self, request):
        """Prevent adding claims from admin - only via student interface"""
        return False
    
    actions = ['approve_claims', 'reject_claims', 'ban_user_7days', 'ban_user_30days', 'ban_user_permanent']
    
    def approve_claims(self, request, queryset):
        """Admin action to approve claims"""
        count = 0
        for claim in queryset.filter(status='pending'):
            claim.status = 'approved'
            claim.item.is_claimed = True
            claim.item.save()
            claim.save(update_fields=['status'])  # Ensure signal detects status change
            count += 1
        self.message_user(request, f"✓ Approved {count} claim(s). Notification emails sent to users.")
    approve_claims.short_description = "Approve selected claims"
    
    def reject_claims(self, request, queryset):
        """Admin action to reject claims"""
        pending_claims = queryset.filter(status='pending')
        updated = 0
        for claim in pending_claims:
            claim.status = 'rejected'
            claim.save(update_fields=['status'])  # Ensure signal detects status change
            updated += 1
        self.message_user(request, f"✗ Rejected {updated} claim(s). Notification emails sent to users.")
    reject_claims.short_description = "Reject selected claims"
    
    def ban_user_7days(self, request, queryset):
        """Ban user for 7 days for fake claims"""
        updated = 0
        for claim in queryset:
            user = claim.user
            ban_until = timezone.now() + timedelta(days=7)
            user_ban, created = UserBan.objects.get_or_create(user=user)
            user_ban.is_banned = True
            user_ban.banned_until = ban_until
            user_ban.ban_reason = f"Fake or fraudulent claim request detected (Item: {claim.item.title})"
            user_ban.save()
            updated += 1
        self.message_user(request, f"✓ Banned {updated} user(s) for 7 days due to fake claims.")
    ban_user_7days.short_description = "⛔ Ban user for 7 days (Fake claim)"
    
    def ban_user_30days(self, request, queryset):
        """Ban user for 30 days for fake claims"""
        updated = 0
        for claim in queryset:
            user = claim.user
            ban_until = timezone.now() + timedelta(days=30)
            user_ban, created = UserBan.objects.get_or_create(user=user)
            user_ban.is_banned = True
            user_ban.banned_until = ban_until
            user_ban.ban_reason = f"Fake or fraudulent claim request detected (Item: {claim.item.title})"
            user_ban.save()
            updated += 1
        self.message_user(request, f"✓ Banned {updated} user(s) for 30 days due to fake claims.")
    ban_user_30days.short_description = "⛔ Ban user for 30 days (Fake claim)"
    
    def ban_user_permanent(self, request, queryset):
        """Permanently ban user for fake claims"""
        updated = 0
        for claim in queryset:
            user = claim.user
            user_ban, created = UserBan.objects.get_or_create(user=user)
            user_ban.is_banned = True
            user_ban.banned_until = None  # Permanent ban
            user_ban.ban_reason = f"Permanent ban: Fake or fraudulent claim request detected (Item: {claim.item.title})"
            user_ban.save()
            updated += 1
        self.message_user(request, f"✓ Permanently banned {updated} user(s) due to fake claims.")
    ban_user_permanent.short_description = "⛔ Permanently ban user (Fake claim)"


admin.site.register(Item, ItemAdmin)
admin.site.register(ClaimRequest, ClaimRequestAdmin)


class UserBanAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_banned', 'ban_status', 'date_banned')
    list_filter = ('is_banned', 'date_banned')
    search_fields = ('user__username', 'user__email', 'ban_reason')
    readonly_fields = ('date_banned', 'user')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'date_banned')
        }),
        ('Ban Status', {
            'fields': ('is_banned', 'banned_until')
        }),
        ('Ban Reason', {
            'fields': ('ban_reason',),
            'classes': ('collapse',)
        }),
    )
    
    def ban_status(self, obj):
        """Display current ban status"""
        if not obj.is_banned:
            return "❌ Not Banned"
        if obj.banned_until is None:
            return "🔴 Permanently Banned"
        if obj.is_currently_banned():
            remaining = obj.banned_until - timezone.now()
            days = remaining.days
            hours = remaining.seconds // 3600
            return f"⏰ Temporarily Banned ({days}d {hours}h remaining)"
        else:
            return "✅ Ban Expired"
    ban_status.short_description = "Current Status"
    
    def has_add_permission(self, request):
        """Allow admins to manage bans only through actions"""
        return False


admin.site.register(UserBan, UserBanAdmin)