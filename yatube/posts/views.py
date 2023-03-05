from django.shortcuts import render, get_object_or_404
from posts.forms import PostForm
from .models import Group, Post, User, Comment
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from .forms import CommentForm
from .models import Follow


def paginator(request, posts):
    SELECT_LIMIT = 10
    paginator = Paginator(posts.order_by("-pub_date"), SELECT_LIMIT)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return page_obj


# @cache_page(20)
def index(request):
    post_list = Post.objects.all().order_by("-pub_date")
    page_obj = paginator(request, post_list)
    context = {
        "page_obj": page_obj,
    }
    return render(request, "posts/index.html", context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.filter(group=group)
    page_obj = paginator(request, post_list)
    context = {
        "group": group,
        "page_obj": page_obj,
    }
    return render(request, "posts/group_list.html", context)


# @login_required
def profile(request, username):
    author = User.objects.get(username__exact=username)
    post_list = author.posts.order_by("-pub_date")
    post_count = post_list.count()
    following = (request.user.is_authenticated
                 and author.following.filter(user=request.user).exists())
    page_obj = paginator(request, post_list)
    context = {
        "page_obj": page_obj,
        "author": author,
        "post_count": post_count,
        'following': following,
    }
    return render(request, "posts/profile.html", context)


def post_detail(request, post_id):
    # post = get_object_or_404(Post, pk=post_id)
    # posts = Post.objects.filter(author=post.author)
    # post_count = posts.count()
    post = get_object_or_404(Post, pk=post_id)
    posts = Post.objects.filter(author=post.author)
    post_count = posts.count()
    comments = Comment.objects.filter(post=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.save()
            form = CommentForm()
    else:
        form = CommentForm()
    context = {
        "post": post,
        "post_count": post_count,
        "form": form,
        "comments": comments,

    }
    return render(request, "posts/post_detail.html", context)


@login_required
def create_post(request):
    if request.method == "POST":
        form = PostForm(request.POST)

        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect("posts:profile", request.user)

    form = PostForm()
    return render(request, "posts/create_post.html", {"form": form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.user != post.author:
        return redirect("posts:post_detail", post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id=post_id)

    context = {
        "form": form,
        "is_edit": True,
        "post_id": post_id,
    }

    return render(request, "posts/create_post.html", context)


@login_required
def add_comment(request, post_id):
    # Получите пост и сохраните его в переменную post.
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    title = 'Публикации избранных авторов'
    posts = Post.objects.filter(author__following__user=request.user)
    # paginator = Paginator(posts, 10)
    # posts = Post.objects.all().order_by("-pub_date")
    page_obj = paginator(request, posts)
    # page_number = request.GET.get('page')
    # page_obj = paginator.get_page(page_number)
    context = {
        'title': title,
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    follow_author = get_object_or_404(User, username=username)
    if follow_author != request.user and (
        not request.user.follower.filter(author=follow_author).exists()
    ):
        Follow.objects.create(
            user=request.user,
            author=follow_author
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    follow_author = get_object_or_404(User, username=username)
    data_follow = request.user.follower.filter(author=follow_author)
    if data_follow.exists():
        data_follow.delete()
    return redirect('posts:profile', username)
