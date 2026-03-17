from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from .models import ClaimRequest


@receiver(post_save, sender=User)
def send_credentials_email(sender, instance, created, **kwargs):
    """
    Signal handler that sends username and password to user's email
    when a new user is created by admin in Django admin panel.
    """
    if created:
        # Only send email if user has an email address
        if instance.email:
            subject = "Welcome to SLT Portal - Your Account Credentials"
            
            message = f"""
Hello {instance.first_name or instance.username},

Your account has been created on the SLT Portal (Lost & Found System).

Here are your login credentials:

Username: {instance.username}
Password: (You may have set this during account creation)

Please log in at: http://localhost:8000/
(Update the URL to match your deployment)

Role: Student

If you have any issues logging in, please contact the administration.

Best regards,
SLT Portal Administration
            """
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [instance.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error sending email to {instance.email}: {str(e)}")


@receiver(post_save, sender=ClaimRequest)
def send_claim_status_email(sender, instance, created, update_fields, **kwargs):
    """
    Signal handler that sends email notification when a claim is approved or rejected.
    """
    # Only send email if status was updated (not on creation)
    if not created:
        # Check if status field was updated
        if update_fields is None or 'status' in update_fields:
            user = instance.user
            item = instance.item
            
            if user.email:
                if instance.status == 'approved':
                    subject = f"Your Claim Request Approved - {item.title}"
                    message = f"""
Hello {user.first_name or user.username},

Good news! Your claim request has been APPROVED.

Item Details:
- Title: {item.title}
- Type: {item.item_type}
- Location: {item.location}
- Description: {item.description}

Please contact the administrator for further instructions on how to collect or finalize this claim.

Best regards,
SLT Portal Administration
                    """
                elif instance.status == 'rejected':
                    subject = f"Your Claim Request Rejected - {item.title}"
                    message = f"""
Hello {user.first_name or user.username},

Your claim request has been REJECTED.

Item Details:
- Title: {item.title}
- Type: {item.item_type}
- Location: {item.location}

You can submit another claim request if needed. If you have any questions, please contact the administrator.

Best regards,
SLT Portal Administration
                    """
                else:
                    return  # No email for other statuses
                
                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=False,
                    )
                except Exception as e:
                    print(f"Error sending email to {user.email}: {str(e)}")

