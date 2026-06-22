import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        await self.send_chat_history()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'delete_message':
            message_id = data.get('message_id')
            success = await self.delete_message_db(message_id, self.user)
            if success:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'message_deleted',
                        'message_id': message_id
                    }
                )
            return

        if action == 'message':
            message_text = data['message']
            msg_obj = await self.save_message(self.room_name, self.user, message_text)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message_id': msg_obj['id'],
                    'message': msg_obj['content'],
                    'username': msg_obj['username'],
                    'timestamp': msg_obj['timestamp']
                }
            )
            return

        if action == 'typing':
            is_typing = data.get('is_typing', False)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_typing',
                    'username': self.user.username,
                    'is_typing': is_typing
                }
            )
            return

    async def message_deleted(self, event):
        await self.send(text_data=json.dumps({
            'action': 'delete',
            'message_id': event['message_id']
        }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'action': 'message',
            'message_id': event['message_id'], 
            'message': event['message'],
            'username': event['username'],
            'timestamp': event['timestamp']
        }))

    async def user_typing(self, event):
        await self.send(text_data=json.dumps({
            'action': 'typing',
            'username': event['username'],
            'is_typing': event['is_typing']
        }))

    async def send_chat_history(self):
        history = await self.get_history(self.room_name)
        await self.send(text_data=json.dumps({
            'action': 'history',
            'history': history
        }))


    @database_sync_to_async
    def delete_message_db(self, message_id, user):
        try:
            msg = Message.objects.get(id=message_id, sender=user)
            msg.is_deleted = True
            msg.save()
            return True
        except Message.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, room_name, user, message_text):
        room, _ = ChatRoom.objects.get_or_create(name=room_name)
        msg = Message.objects.create(room=room, sender=user, content=message_text)
        return {
            'id': msg.id,
            'content': msg.content,
            'username': msg.sender.username,
            'timestamp': msg.timestamp.strftime('%H:%M:%S')
        }

    @database_sync_to_async
    def get_history(self, room_name):
        room, _ = ChatRoom.objects.get_or_create(name=room_name)
        messages = Message.objects.filter(room=room, is_deleted=False).order_by('-timestamp')[:20]
        return [{
            'id': msg.id,
            'username': msg.sender.username,
            'message': msg.content,
            'timestamp': msg.timestamp.strftime('%H:%M:%S')
        } for msg in reversed(messages)]