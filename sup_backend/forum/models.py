import math
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Thread(models.Model):
    author = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name='forum_threads'
    )
    title = models.CharField(max_length=200)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    score = models.FloatField(default=0.0, db_index=True)
    is_visible = models.BooleanField(default=True)
    ai_replied = models.BooleanField(default=False)

    class Meta:
        ordering = ['-score', '-created_at']

    def __str__(self):
        return self.title

    @property
    def display_author(self):
        if self.author and not self.author.username.startswith('guest_'):
            return self.author.username
        return 'anonymous'

    def update_score(self):
        """
        Score = reaction signal * recency decay.
        Negative/absent engagement sinks threads naturally.
        Run whenever reactions or human replies change.
        """
        reaction_count = self.reactions.count()
        human_reply_count = self.replies.filter(is_ai=False).count()

        # Engagement numerator
        engagement = reaction_count * 2 + human_reply_count

        # Recency decay: half-life ~72 hours
        age_hours = (timezone.now() - self.created_at).total_seconds() / 3600
        decay = math.exp(-0.0096 * age_hours)  # ln(2)/72 ≈ 0.0096

        self.score = engagement * decay
        self.save(update_fields=['score'])


class Reply(models.Model):
    thread = models.ForeignKey(Thread, related_name='replies', on_delete=models.CASCADE)
    author = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name='forum_replies'
    )
    body = models.TextField()
    is_ai = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    @property
    def display_author(self):
        if self.is_ai:
            return 'salaryfree'
        if self.author and not self.author.username.startswith('guest_'):
            return self.author.username
        return 'anonymous'


class Reaction(models.Model):
    HELPFUL = 'helpful'
    RELATABLE = 'relatable'
    INSPIRING = 'inspiring'
    REACTION_TYPES = [
        (HELPFUL, 'Helpful'),
        (RELATABLE, 'Relatable'),
        (INSPIRING, 'Inspiring'),
    ]

    thread = models.ForeignKey(Thread, related_name='reactions', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_reactions')
    reaction_type = models.CharField(max_length=20, choices=REACTION_TYPES)

    class Meta:
        unique_together = ('thread', 'user', 'reaction_type')
