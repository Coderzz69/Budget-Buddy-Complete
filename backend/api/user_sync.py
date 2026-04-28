import time

from django.db import OperationalError, transaction

from .models import User, Account


SQLITE_LOCK_RETRY_DELAYS = (0.1, 0.2, 0.4)


def sync_user_record(*, clerk_id, email, name=None, phone_number=None, profile_pic=None, currency='INR'):
    last_error = None

    for attempt, delay in enumerate((*SQLITE_LOCK_RETRY_DELAYS, None), start=1):
        try:
            with transaction.atomic():
                user = User.objects.filter(clerkId=clerk_id).first()
                if not user:
                    user = User.objects.filter(email=email).first()
                
                created = False
                if not user:
                    user = User(
                        clerkId=clerk_id,
                        email=email,
                        name=name,
                        phoneNumber=phone_number,
                        profilePic=profile_pic,
                        currency=currency or 'INR'
                    )
                    user.save()
                    created = True
                
                if not created:
                    # Update fields only if they have changed or were empty
                    changed = False
                    if user.clerkId != clerk_id:
                        user.clerkId = clerk_id
                        changed = True
                    if email and user.email != email:
                        user.email = email
                        changed = True
                    if name and not user.name:
                        user.name = name
                        changed = True
                    if phone_number and not user.phoneNumber:
                        user.phoneNumber = phone_number
                        changed = True
                    if profile_pic and user.profilePic != profile_pic:
                        user.profilePic = profile_pic
                        changed = True
                    if changed:
                        user.save()
                
                # Ensure user has at least one account to pass onboarding
                if not Account.objects.filter(user=user).exists():
                    Account.objects.create(
                        user=user,
                        name="Main Account",
                        type="cash",
                        balance=0.0
                    )

                return user, created
        except OperationalError as exc:
            if 'database is locked' not in str(exc).lower() or delay is None:
                raise
            last_error = exc
            time.sleep(delay)

    if last_error:
        raise last_error
