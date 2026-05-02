import uuid
from django.db import models


class User(models.Model):
    """Mirrors Prisma User model."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    clerkId = models.CharField(max_length=255, unique=True, db_column='clerkId')
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    phoneNumber = models.CharField(max_length=50, blank=True, null=True, db_column='phoneNumber')
    profilePic = models.TextField(blank=True, null=True, db_column='profilePic')
    currency = models.CharField(max_length=10, default='INR')
    createdAt = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updatedAt = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'User'

    @property
    def is_authenticated(self):
        return True

    def __str__(self):
        return f'{self.email} ({self.clerkId})'


class Account(models.Model):
    """Mirrors Prisma Account model."""
    ACCOUNT_TYPES = [
        ('cash', 'Cash'),
        ('bank', 'Bank'),
        ('card', 'Card'),
        ('wallet', 'Wallet'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts', db_column='userId')
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    balance = models.FloatField(default=0.0)
    createdAt = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'Account'

    def __str__(self):
        return f'{self.name} ({self.type})'

    @property
    def userId(self):
        return str(self.user_id)


class Category(models.Model):
    """Mirrors Prisma Category model. userId=None means global/system category."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='categories',
        null=True, blank=True, db_column='userId'
    )
    name = models.CharField(max_length=255)
    icon = models.CharField(max_length=100, blank=True, null=True)
    color = models.CharField(max_length=20, blank=True, null=True)
    createdAt = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'Category'
        # Mirrors: @@unique([userId, name])
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'name'],
                name='unique_user_category_name',
                condition=models.Q(user__isnull=False)
            )
        ]

    def __str__(self):
        return self.name

    @property
    def userId(self):
        return str(self.user_id) if self.user_id else None


class Transaction(models.Model):
    """Mirrors Prisma Transaction model."""
    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions', db_column='userId')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions', db_column='accountId')
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, related_name='transactions',
        null=True, blank=True, db_column='categoryId'
    )
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.FloatField()
    note = models.TextField(blank=True, null=True)
    occurredAt = models.DateTimeField(db_column='occurredAt')
    createdAt = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    
    # ML & Behavior Engine Flags
    is_recurring = models.BooleanField(default=False, db_index=True)
    is_anomaly = models.BooleanField(default=False)

    class Meta:
        db_table = 'Transaction'
        indexes = [
            models.Index(fields=['user'], name='tx_user_idx'),
            models.Index(fields=['occurredAt'], name='tx_occurred_idx'),
            models.Index(fields=['account'], name='tx_account_idx'),
            models.Index(fields=['user', 'occurredAt'], name='tx_usr_occ_idx'),
            models.Index(fields=['user', 'is_recurring'], name='tx_usr_rec_idx'),
        ]
        ordering = ['-occurredAt']

    def __str__(self):
        return f'{self.type} {self.amount} @ {self.occurredAt}'

    @property
    def userId(self):
        return str(self.user_id)

    @property
    def accountId(self):
        return str(self.account_id)

    @property
    def categoryId(self):
        return str(self.category_id) if self.category_id else None


class Budget(models.Model):
    """Mirrors Prisma Budget model."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets', db_column='userId')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='budgets', db_column='categoryId')
    month = models.DateTimeField()  # first day of month
    limit = models.FloatField()
    createdAt = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'Budget'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'category', 'month'],
                name='unique_user_category_month'
            )
        ]

    def __str__(self):
        return f'Budget {self.category} {self.month:%Y-%m}'

    @property
    def userId(self):
        return str(self.user_id)

    @property
    def categoryId(self):
        return str(self.category_id)


class NormalizedMerchant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='normalized_merchants', null=True, blank=True, db_column='userId')
    rawName = models.CharField(max_length=255, unique=True, db_column='rawName')
    normalizedName = models.CharField(max_length=255, db_column='normalizedName')
    defaultCategory = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='normalized_merchants', db_column='categoryId')
    confidence = models.FloatField(default=1.0)
    createdAt = models.DateTimeField(auto_now_add=True, db_column='createdAt')
    updatedAt = models.DateTimeField(auto_now=True, db_column='updatedAt')

    class Meta:
        db_table = 'NormalizedMerchant'

    def __str__(self):
        return f'{self.rawName} -> {self.normalizedName}'


class ModelPrediction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='prediction', db_column='transactionId')
    modelName = models.CharField(max_length=255, db_column='modelName')
    prediction = models.CharField(max_length=255)
    confidence = models.FloatField()
    metadata = models.JSONField(null=True, blank=True)
    createdAt = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'ModelPrediction'


class RecurringPattern(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions', db_column='userId')
    merchantName = models.CharField(max_length=255, db_column='merchantName', db_index=True)
    
    expected_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    frequency = models.CharField(max_length=50, choices=[('weekly', 'Weekly'), ('monthly', 'Monthly'), ('annual', 'Annual')], default='monthly')
    
    lastOccurredAt = models.DateTimeField(db_column='lastOccurredAt')
    next_due_date = models.DateField(db_column='nextExpectedAt', db_index=True)
    
    confidence_score = models.FloatField()
    isActive = models.BooleanField(default=True, db_column='isActive')
    createdAt = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'RecurringPattern'
        unique_together = ('user', 'merchantName')


class InsightSnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='insight_snapshots', db_column='userId')
    kind = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    body = models.TextField()
    data = models.JSONField(null=True, blank=True)
    expiresAt = models.DateTimeField(null=True, blank=True, db_column='expiresAt')
    isRead = models.BooleanField(default=False, db_column='isRead')
    createdAt = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'InsightSnapshot'
        indexes = [
            models.Index(fields=['user'], name='insight_user_idx'),
            models.Index(fields=['kind'], name='insight_kind_idx'),
        ]

class MLTrainingRow(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ml_training_rows', db_column='userId')
    occurredAt = models.DateTimeField(db_column='occurredAt')
    amount = models.FloatField()
    descriptionRaw = models.TextField(db_column='descriptionRaw')
    predictedCategory = models.CharField(max_length=255, null=True, blank=True, db_column='predictedCategory')
    confidence = models.FloatField(null=True, blank=True)
    createdAt = models.DateTimeField(auto_now_add=True, db_column='createdAt')

    class Meta:
        db_table = 'MLTrainingRow'
        indexes = [
            models.Index(fields=['user'], name='ml_training_user_idx'),
        ]

class UserBehaviorProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='behavior_profile', db_column='userId')
    
    average_monthly_burn = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    weekend_overspend_ratio = models.FloatField(default=1.0)
    salary_credit_date_expected = models.PositiveSmallIntegerField(null=True, blank=True)
    savings_consistency_score = models.FloatField(default=0.0)
    
    last_computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'UserBehaviorProfile'

class Alert(models.Model):
    ALERT_TYPES = [
        ('low_balance', 'Low Balance Prediction'),
        ('unusual_spend', 'Unusual Spend Detected'),
        ('weekend_warning', 'Weekend Overspend Warning'),
        ('subscription_due', 'Subscription Due Soon')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alerts', db_column='userId')
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    
    issued_at = models.DateTimeField(auto_now_add=True, db_index=True)
    metadata = models.JSONField(blank=True, null=True)

    class Meta:
        db_table = 'Alert'
        ordering = ['-issued_at']

class PredictionCache(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='predictions', db_column='userId')
    model_version = models.CharField(max_length=50)
    
    trajectory_data = models.JSONField() 
    predicted_runout_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'PredictionCache'
        indexes = [
            models.Index(fields=['user', '-created_at'])
        ]


class ModelRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_name = models.CharField(max_length=100)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('running', 'Running'), ('success', 'Success'), ('failed', 'Failed')])
    users_processed = models.IntegerField(default=0)
    error_logs = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'ModelRun'


class Goal(models.Model):
    """Represents a user-defined savings goal (e.g. 'Buy Honda Shine')."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals', db_column='userId')
    name = models.CharField(max_length=255)
    target_amount = models.FloatField()
    saved_amount = models.FloatField(default=0.0)
    monthly_contribution = models.FloatField()
    icon = models.CharField(max_length=100, blank=True, null=True, default='target')
    color = models.CharField(max_length=20, blank=True, null=True, default='#38BDF8')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Goal'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} (target: {self.target_amount})'

    @property
    def months_remaining(self):
        remaining = self.target_amount - self.saved_amount
        if remaining <= 0:
            return 0
        if self.monthly_contribution <= 0:
            return None
        import math
        return math.ceil(remaining / self.monthly_contribution)

    @property
    def progress_pct(self):
        if self.target_amount <= 0:
            return 0.0
        return round(min((self.saved_amount / self.target_amount) * 100, 100), 1)

