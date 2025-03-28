from django.urls import path, reverse_lazy
from blog.views import (
    PostListView,
    CategoryListView,
    PostDetailView,
    PostCreateView,
    PostsComment,
    profile_view,
    ProfileUpdateView,
    PostUpdateView,
    CommentDelete,
    PostDeleteView,
    CommentUpdate)
from django.contrib.auth import views


app_name = 'blog'

urlpatterns = [
    path('', PostListView.as_view(), name='index'),
    path('posts/create/', PostCreateView.as_view(), name='create_post'),
    path('posts/<int:post_id>/', PostDetailView.as_view(), name='detail'),
    path(
        'posts/<int:post_id>/edit/',
        PostUpdateView.as_view(),
        name='edit_post'),
    path(
        'posts/<int:post_id>/delete/',
        PostDeleteView.as_view(),
        name='delete_post'),
    path('posts/<int:post_id>/comment/',
         PostsComment.as_view(),
         name='add_comment'),
    path('posts/<int:post_id>/comment/<int:comment_id>',
         CommentUpdate.as_view(),
         name='edit_comment'),
    path('posts/<int:post_id>/delete_comment/<int:comment_id>/',
         CommentDelete.as_view(),
         name='delete_comment'),
    path(
        'category/<slug:category_slug>/',
        CategoryListView.as_view(),
        name='category'),

    path('profile/<str:username>/', profile_view, name='profile'),

    path('edit-profile/', ProfileUpdateView.as_view(
        template_name='blog/user.html',
    ), name='edit_profile'),

    path('password-change/', views.PasswordChangeView.as_view(
        template_name='registration/password_change_form.html',
        success_url=reverse_lazy('blog:profile')
    ), name='password_change'),
]
