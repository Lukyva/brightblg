from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import models
from .models import Post, Category, Comment
from .forms import CommentForm, SignupForm
from django.shortcuts import get_object_or_404
from hitcount.views import HitCountDetailView
from django.db.models import Count
from hitcount.models import HitCount
from django.contrib.auth.forms import UserCreationForm
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST) # CHANGED
        if form.is_valid():
            form.save()
            messages.success(request, "Account created! You can now login.")
            return redirect('login')
    else:
        form = SignupForm() # CHANGED
    
    return render(request, 'registration/signup.html', {'form': form})  
    

def home(request):
    posts = Post.objects.filter(published=True).order_by('-created')[:6]
    
    # FIX: Get top 3 most viewed posts using our 'views' field
    featured = Post.objects.filter(published=True)\
        .order_by('-views')[:3] # <-- use views field directly
        
    categories = Category.objects.all()
    
    return render(request, 'home.html', {
        'posts': posts,
        'featured': featured,
        'categories': categories
    })
    
def post_list(request):
    posts = Post.objects.filter(published=True).order_by('-created')
    query = request.GET.get('q')
    if query: posts = posts.filter(Q(title__icontains=query) | Q(content__icontains=query))
    paginator = Paginator(posts, 9)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'post_list.html', {'posts': page})


class PostDetailView(HitCountDetailView):
    model = Post
    template_name = 'post_detail.html'
    context_object_name = 'post'
    slug_field = 'slug'
    count_hit = False
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # INCREASE VIEWS BY 1 EVERY TIME PAGE LOADS
        obj.views = models.F('views') + 1 
        obj.save(update_fields=['views'])
        # refresh from db so F() works
        obj.refresh_from_db()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['total_comments'] = self.object.comments.filter(active=True).count() # 24
    
        # 2. ONLY TOP LEVEL for displaying the first few
        top_level_comments = self.object.comments.filter(parent__isnull=True, active=True).order_by('-created')
        
        context['comments'] = top_level_comments
        context['latest_top_comment'] = top_level_comments.first()
        context['form'] = CommentForm()
        context['hits'] = self.object.views # USE OUR NEW FIELD
        return context

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        post = self.get_object()
        form = CommentForm(data=request.POST)
        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.post = post
            new_comment.user = request.user
            new_comment.active = True # make sure it's active
            parent_id = form.cleaned_data.get('parent_id')
            if parent_id: # if it's a reply
                new_comment.parent = Comment.objects.get(id=parent_id)
            new_comment.save()
        return self.get(request, *args, **kwargs)

@login_required
def like_post(request, slug):

    if request.method != "POST":
        return JsonResponse(
            {"error": "POST required"},
            status=400
        )

    post = get_object_or_404(Post, slug=slug)
    user = request.user

    # Check whether this user has already liked the post
    already_liked = post.likes.filter(id=user.id).exists()

    if already_liked:
        # User already liked it -> UNLIKE
        post.likes.remove(user)
        liked = False
    else:
        # User hasn't liked it -> LIKE
        post.likes.add(user)
        liked = True

    return JsonResponse({
        "liked": liked,
        "total_likes": post.likes.count()
    })
def category_posts(request, slug):
    category = get_object_or_404(Category, slug=slug)
    posts = Post.objects.filter(category=category, published=True).order_by('-created')
    
    return render(request, 'category.html', {
        'category': category,
        'posts': posts
    })
    
def comment_thread(request, comment_id):

    root_comment = get_object_or_404(
        Comment,
        id=comment_id,
        active=True
    )

    post = root_comment.post

    replies = root_comment.replies.filter(
        active=True
    ).order_by('created')


    if request.method == 'POST':

        if not request.user.is_authenticated:
            return JsonResponse(
                {'error': 'Login required'},
                status=403
            )

        form = CommentForm(request.POST)

        if form.is_valid():

            new_comment = form.save(commit=False)

            new_comment.post = post
            new_comment.user = request.user
            new_comment.active = True

            # Always reply to the root comment
            new_comment.parent = root_comment

            new_comment.save()

            # AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':

                replies = root_comment.replies.filter(
                    active=True
                ).order_by('created')

                context = {
                    'root_comment': root_comment,
                    'post': post,
                    'replies': replies,
                    'form': CommentForm(),
                }

                return render(
                    request,
                    'partials/comment_thread_modal.html',
                    context
                )

            return redirect(
                'comment_thread',
                comment_id=root_comment.id
            )

    else:

        form = CommentForm()


    context = {
        'root_comment': root_comment,
        'post': post,
        'replies': replies,
        'form': form,
    }


    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':

        return render(
            request,
            'partials/comment_thread_modal.html',
            context
        )


    return render(
        request,
        'comment_thread.html',
        context
    )
    
def all_comments(request, slug):

    post = get_object_or_404(
        Post,
        slug=slug
    )


    top_comments = post.comments.filter(
        parent__isnull=True,
        active=True
    ).order_by('-created')


    # Build flat replies
    for c in top_comments:

        c.all_replies_flat = post.comments.filter(
            active=True
        ).filter(
            Q(parent=c) |
            Q(parent__parent=c) |
            Q(parent__parent__parent=c)
        ).order_by('created')


    total_comments = post.comments.filter(
        active=True
    ).count()


    if request.method == 'POST':

        if not request.user.is_authenticated:

            return JsonResponse(
                {'error': 'Login required'},
                status=403
            )


        form = CommentForm(request.POST)


        if form.is_valid():

            new_comment = form.save(commit=False)

            new_comment.post = post
            new_comment.user = request.user
            new_comment.active = True


            parent_id = request.POST.get('parent_id')


            if parent_id:

                parent_comment = get_object_or_404(
                    Comment,
                    id=parent_id,
                    active=True
                )


                # Always reply to top-level comment
                if parent_comment.parent:

                    new_comment.parent = parent_comment.parent

                else:

                    new_comment.parent = parent_comment


            new_comment.save()


            # Rebuild comments after adding new comment
            top_comments = post.comments.filter(
                parent__isnull=True,
                active=True
            ).order_by('-created')


            for c in top_comments:

                c.all_replies_flat = post.comments.filter(
                    active=True
                ).filter(
                    Q(parent=c) |
                    Q(parent__parent=c) |
                    Q(parent__parent__parent=c)
                ).order_by('created')


            total_comments = post.comments.filter(
                active=True
            ).count()


            form = CommentForm()


            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':

                context = {
                    'post': post,
                    'comments': top_comments,
                    'total_comments': total_comments,
                    'form': form,
                }

                return render(
                    request,
                    'partials/comments_modal.html',
                    context
                )


            return redirect(
                'all_comments',
                slug=post.slug
            )


    else:

        form = CommentForm()


    context = {
        'post': post,
        'comments': top_comments,
        'total_comments': total_comments,
        'form': form,
    }


    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':

        return render(
            request,
            'partials/comments_modal.html',
            context
        )


    return render(
        request,
        'all_comments.html',
        context
    )

    
    