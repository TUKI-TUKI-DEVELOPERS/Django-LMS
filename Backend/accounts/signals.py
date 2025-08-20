from .utils import (
    generate_student_credentials,
    generate_lecturer_credentials,
    send_new_account_email,
)


def post_save_account_receiver(sender, instance=None, created=False, *args, **kwargs):
    """
    Send email notification
    """
    if created:
        # Check if this is a public registration (user chose their own username/password)
        # Skip auto-generation if the user already has a proper username (not empty)
        is_public_registration = hasattr(instance, '_public_registration') and instance._public_registration
        
        if not is_public_registration:
            if instance.is_student:
                username, password = generate_student_credentials()
                instance.username = username
                instance.set_password(password)
                instance.save()
                # Send email with the generated credentials
                send_new_account_email(instance, password)

            if instance.is_lecturer:
                username, password = generate_lecturer_credentials()
                instance.username = username
                instance.set_password(password)
                instance.save()
                # Send email with the generated credentials
                send_new_account_email(instance, password)
