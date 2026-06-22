from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.db.models import Q
from .models import ChatRoom, Message, Profile

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import ChatRoom, Message, Profile

@login_required
def chat_index(request):
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            bio = request.POST.get('bio', '').strip()
            if bio:
                profile.bio = bio
            if 'avatar' in request.FILES:
                profile.avatar = request.FILES['avatar']
            profile.save()
            return redirect('chat:index')
            
        elif 'create_group' in request.POST:
            group_name = request.POST.get('group_name', '').strip()
            if group_name:
                room = ChatRoom.objects.create(
                    name=f"group_{group_name}_{user.id}", 
                    display_name=group_name, 
                    room_type='group'
                )
                room.members.add(user)
                return redirect('chat:room', room_name=room.name)

    search_query = request.GET.get('search', '').strip()
    search_results = []
    if search_query:
        search_results = User.objects.filter(username__icontains=search_query).exclude(id=user.id)

    rooms = user.chat_rooms.exclude(deleted_for=user).order_by('-created_at')
    processed_rooms = []
    for r in rooms:
        if r.room_type == 'pv':
            other_user = r.members.exclude(id=user.id).first()
            if other_user:
                Profile.objects.get_or_create(user=other_user)
                processed_rooms.append({
                    'obj': r,
                    'title': other_user.username,
                    'avatar': other_user.profile.avatar.url,
                    'type': 'Chat'
                })
        else:
            processed_rooms.append({
                'obj': r,
                'title': r.display_name,
                'avatar': '/media/avatars/default.png',
                'type': 'Group'
            })

    return render(request, 'chat/index.html', {
        'rooms': processed_rooms,
        'search_results': search_results,
        'search_query': search_query
    })

@login_required
def room(request, room_name):
    room_obj = get_object_or_404(ChatRoom, name=room_name)
    chat_partner = None
    if room_obj.room_type == 'pv':
        chat_partner = room_obj.members.exclude(id=request.user.id).first()
        if chat_partner:
            Profile.objects.get_or_create(user=chat_partner)

    return render(request, 'chat/room.html', {
        'room_name': room_name,
        'room': room_obj,
        'chat_partner': chat_partner
    })

@login_required
def start_pv(request, username):
    other_user = get_object_or_404(User, username=username)
    user = request.user
    
    room_name = f"pv_{min(user.id, other_user.id)}_{max(user.id, other_user.id)}"
    
    room, created = ChatRoom.objects.get_or_create(name=room_name, room_type='pv')
    if created:
        room.members.add(user, other_user)
    
    if room.deleted_for.filter(id=user.id).exists():
        room.deleted_for.remove(user)
        
    return redirect('chat:room', room_name=room.name)

@login_required
def delete_chat(request, room_name):
    room = get_object_or_404(ChatRoom, name=room_name)
    room.deleted_for.add(request.user)
    return redirect('chat:index')

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user)
            login(request, user)
            return redirect('chat:index')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})