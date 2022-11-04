
from urllib import request
from .models import Profile,Post,LikePost,FollowersCount
from django.shortcuts import render,redirect
from django.contrib.auth.models import User,auth
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib import messages
from itertools import chain
import random
# Create your views here.
@login_required(login_url = 'signin')
def index(request):
    user_object = User.objects.get(username = request.user.username)
    user_profile = Profile.objects.get(user = user_object)
    #User Feed
    user_following_list = []
    feed = []
    user_following = FollowersCount.objects.filter(follower = request.user.username)
    for users in user_following:
        user_following_list.append(users.user)
    for username in user_following_list:
        feed.append(Post.objects.filter(user = username))
    feed_list = list(chain(*feed))
    
    #user sugestion stats
    all_users = User.objects.all()
    user_following_all = []
    for user in user_following:
        user_list = User.objects.get(username = user.user)
        user_following_all.append(user_list)
    new_suggestion_list = [x for x in list(all_users) if (x not in list(user_following_all))]
    current_user = User.objects.filter(username = request.user.username)
    new_suggestion_list = [x for x in new_suggestion_list if(x not in list(current_user))]
    random.shuffle(new_suggestion_list)

    username_profile = []
    username_profile_list = []

    for users in new_suggestion_list:
        username_profile.append(users.id)
    
    for id in username_profile:
        username_profile_list.append(Profile.objects.filter(id_user = id))
    suggestion_username_profile_list = list(chain(*username_profile_list))

    return render(request,'index.html',{'user_profile' : user_profile,'posts':feed_list, 'Profile' : Profile,'suggestion_username_profile_list' : suggestion_username_profile_list[:4],})

def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']
        if password == password2:
            if User.objects.filter(email = email).exists():
                messages.info(request,'Email already taken')
                return redirect('signup')
            elif User.objects.filter(username = username).exists():
                messages.info(request,'username already taken')
                return redirect('signup')
            else:
                user = User.objects.create_user(username = username,email = email , password = password)
                user.save()
                #log user in and redirect to setting page
                user_login = auth.authenticate(username = username, password = password)
                auth.login(request,user_login)
                #create a profile for the user
                user_model = User.objects.get(username = username)
                new_profile = Profile.objects.create(user = user_model, id_user = user_model.id)
                new_profile.save()
                return redirect('settings')

        else:
            messages.info(request,'passwords do not match')
            return redirect('signup')

    else:
        return render(request,'signup.html')

@login_required(login_url = 'signin')
def settings(request):
    user_profile = Profile.objects.get(user = request.user)
    if request.method == 'POST':
        if request.FILES.get('image') == None:
            image = user_profile.profileimg
        else:
            image = request.FILES.get('image')
        bio = request.POST['bio']
        location = request.POST['location']
        user_profile.profileimg = image
        user_profile.bio = bio
        user_profile.location = location
        user_profile.save()
        return redirect('settings')

    return render(request,'setting.html',{'user_profile' : user_profile})

def signin(request):
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(username = username , password = password)
        if user is not None:
            auth.login(request, user)
            return redirect('/')
        else:
            messages.info(request , 'Credentials are not Valid')
            return redirect('signin')
    else:
        return render(request,'signin.html')

@login_required(login_url = 'signin')
def logout(request):
    auth.logout(request)
    return redirect('signin')

@login_required(login_url = 'signin')
def like_post(request):
    username = request.user.username
    post_id = request.GET.get('post_id')

    post = Post.objects.get(id = post_id)

    like_fileter = LikePost.objects.filter(post_id = post_id,username = username).first()

    if like_fileter == None:
        new_like = LikePost.objects.create(post_id = post_id, username = username)
        new_like.save()
        post.no_of_likes += 1
        post.save()
        return redirect('/')
    else:
        like_fileter.delete()
        post.no_of_likes -= 1
        post.save()
        return redirect('/')


@login_required(login_url = 'signin')
def upload(request):
    if request.method == 'POST':
        user = request.user.username
        image = request.FILES.get('image_upload')
        caption = request.POST['caption']
        new_post = Post.objects.create(user = user,image = image,caption = caption)
        new_post.save()
        return redirect('/')
    else:
        return redirect('/')
    

@login_required(login_url = 'signin')
def profile(request,pk):
    user_object = User.objects.get(username = pk)
    user_profile = Profile.objects.get(user = user_object)
    user_posts = Post.objects.filter(user = pk)
    number_of_post = len(user_posts)
    follower = request.user.username
    user = pk
    if FollowersCount.objects.filter(follower = follower, user = user).first():
        Button_text = 'Unfollow'
    else:
        Button_text = 'Follow'
    user_followers = len(FollowersCount.objects.filter(user = pk))
    user_following = len(FollowersCount.objects.filter(follower = pk))
    context = {
        'user_object' : user_object,
        'user_profile' : user_profile,
        'user_posts' : user_posts,
        'number_of_post' : number_of_post,
        'button_text' : Button_text,
        'user_followers' : user_followers,
        'user_following' : user_following,
    }
    return render(request , 'profile.html',context)


@login_required(login_url = 'signin')
def follow(request):
    if request.method == 'POST':
        follower = request.POST['follower']
        user = request.POST['user']
        if FollowersCount.objects.filter(follower = follower, user = user).first():
            FollowersCount.objects.filter(follower = follower, user = user).delete()
            return redirect('/profile/' + user)         
        else:
            new_follower = FollowersCount.objects.create(follower = follower,user = user)
            new_follower.save()
            return redirect('/profile/' + user)


    else:
        return redirect('/')

@login_required(login_url = 'signin')
def search(request):
    user_object = User.objects.get(username = request.user.username)
    user_profile = Profile.objects.get(user = user_object)

    if request.method == 'POST':
        username = request.POST['username']
        username_object = User.objects.filter(username__icontains = username )
        username_profile = []
        username_profile_list = []
        for users in username_object:
            username_profile.append(users.id)
        for id in username_profile:
            profile_list = Profile.objects.filter(id_user = id)
            username_profile_list.append(profile_list)
    username_profile_list = list(chain(*username_profile_list))


    return render(request,'search.html',{'user_profile' : user_profile,'username_profile_list':username_profile_list})



