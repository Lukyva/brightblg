"""
URL configuration for brightly_blog project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from blog import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('blog/', views.post_list, name='post_list'),
    path("ckeditor5/", include('django_ckeditor_5.urls')),
    path('blog/<slug:slug>/', views.PostDetailView.as_view(), name='post_detail'),
    path('category/<slug:slug>/', views.category_posts, name='category_posts'),
    path('post/<slug:slug>/like/', views.like_post, name='like_post'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', views.signup, name='signup'),
    path('comment/<int:comment_id>/', views.comment_thread, name='comment_thread'),
    path('post/<slug:slug>/comments/', views.all_comments, name='all_comments'),
    path('post/<slug:slug>/like/', views.like_post, name='like_post'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
