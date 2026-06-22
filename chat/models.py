from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.png', blank=True)
    bio = models.CharField(max_length=255, blank=True, default="سلام! من از سیستم چت استفاده می‌کنم.")

    def __str__(self):
        return self.user.username

class ChatRoom(models.Model):
    ROOM_TYPES = (
        ('pv', 'Private Chat'),
        ('group', 'Group Chat'),
    )
    name = models.CharField(max_length=255, unique=True) 
    display_name = models.CharField(max_length=255, blank=True)
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES, default='pv')
    members = models.ManyToManyField(User, related_name='chat_rooms')
    
    deleted_for = models.ManyToManyField(User, related_name='deleted_rooms', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.display_name if self.room_type == 'group' else self.name

class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']