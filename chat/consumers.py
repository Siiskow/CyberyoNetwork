import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils.timesince import timesince
from datetime import datetime
from .models import Message,Room,KeyPair


class ChatConsumer(AsyncWebsocketConsumer): 
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        #To join the room : 
        await self.get_room()
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code) : 
        #Disconnect from the room 
        await self.channel_layer.group_discard(self.room_group_name,self.channel_name)

    async def receive(self, text_data):
        # Receive message from WebSocket (front end)
        text_data_json = json.loads(text_data)
        type = text_data_json['type']
        

        print('Receive:', type)
        user = self.scope['user']
        username = user.username if user.is_authenticated else 'AnonymousUser'
        print(self.room.isGroupChat)
        if type == 'message':
            message = text_data_json['message']
            print(message)
            # Send message to group / room
            new_message = await self.create_message(message,user,self.room)
            users_in_room_excluding_me = await self.get_second_user(user)
            await self.channel_layer.group_send(
                self.room_group_name, {
                    'first_name' : user.first_name,
                    'last_name' : user.last_name,
                    'second_user_image' : users_in_room_excluding_me,
                    'current_user' : username,
                    'type': 'chat_message',
                    'message': message,
                    'message_id':new_message.id,
                    'created_at_no_timesince':new_message.created_at.isoformat(),
                    'created_at': timesince(new_message.created_at),
                }
            
            )
            print("got here")
        if type == 'delete_message':
            message_id = text_data_json['message_id']
            result_deleting = await self.remove_message(message_id,self.room)
            await self.channel_layer.group_send(
                self.room_group_name,{
                    'current_user' : username,
                    'type':'deleted_Message',
                    'message_id':message_id,
                    'result': result_deleting,
                    'room':self.room.room_id
                }
            )
        if type == 'get_keys':
            public_key, private_key = await self.get_keys()
            await self.send(text_data=json.dumps({
                'type': 'send_keys',
                'public_key': public_key,
                'private_key' : private_key,
            }))


    async def deleted_Message(self,event):
        await self.send(text_data=json.dumps({
            'type':event['type'],
            'message_id': event['message_id'],
            'result':event['result'],
            'room': event['room'],
            'current_user' : event['current_user'],
        }))

    async def chat_message(self, event):
        # Send message to WebSocket (front end)
        await self.send(text_data=json.dumps({
            'type': event['type'],
            'message': event['message'],
            'created_at': event['created_at'],
            'current_user' : event['current_user'],
            'second_user_image' : event['second_user_image'],
            'created_at_no_timesince':event['created_at_no_timesince'],
            'message_id':event['message_id'],
            'first_name' :event['first_name'],
            'last_name' : event['last_name'],
        }))
        print("got here 2")

    @sync_to_async
    def get_room(self):
        self.room = Room.objects.get(room_id=self.room_name)

    @sync_to_async
    def get_keys(self):
        room = Room.objects.get(room_id = self.room)
        public_key = KeyPair.objects.get(room=room).public_key
        private_key = KeyPair.objects.get(room=room).private_key
        return public_key,private_key
        
    
    @sync_to_async
    def create_message(self, message, created_by, room):
        message = Message.objects.create(body=message,created_by=created_by, chat_room = room)
        message.save()
        self.room.messages.add(message)
        return message
    
    @sync_to_async
    def get_second_user(self,user):
        return user.profile_pic.url
    @sync_to_async
    def remove_message(self,message_id,room) : 
        MessageInstance = self.room.messages.get(pk=message_id)
        if MessageInstance.created_by == self.scope['user']:
            MessageInstance.delete()
            return "deleted"
        else:
            return "Error_Deleting"

    
