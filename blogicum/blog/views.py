from django.views.generic import (
    ListView,
    DetailView,
    detail,
    FormView,
    UpdateView,
    DeleteView)
from .models import Post, Category, Comment
from django.utils import timezone
from django.db.models import Count
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import CommentForm, UserProfileForm, PostForm
from django.core.paginator import Paginator
# Create your views here.


def get_published_posts(queryset=None, only_published=True):
    if queryset is None:
        queryset = Post.objects.all()
    if only_published:
        queryset = queryset.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True
        )
    return queryset


def add_comment_count(queryset):
    return queryset.annotate(
        comment_count=Count('comment')).order_by(*Post._meta.ordering)


def paginate_posts(request, posts, per_page=10):
    paginator = Paginator(posts, per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


class PostListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'post_list'
    paginate_by = 10

    def get_queryset(self):
        posts = get_published_posts()
        return add_comment_count(posts).order_by('-pub_date')


class CategoryListView(ListView):
    model = Post
    template_name = 'blog/category.html'
    context_object_name = 'page_obj'
    paginate_by = 10

    def get_queryset(self):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        posts = get_published_posts(self.category.post_set.all())
        return add_comment_count(posts).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'category': self.category,
            'total_posts': self.get_queryset().count()
        })
        return context


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def get_object(self, queryset=None):
        post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        if post.author != self.request.user:
            post = get_object_or_404(
                get_published_posts(),
                pk=self.kwargs['post_id']
            )
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comment_set.all().order_by('created')
        context['form'] = CommentForm()
        return context


def profile_view(request, username):
    profile = get_object_or_404(User, username=username)
    posts = profile.post_set.all()

    if request.user != profile:
        posts = get_published_posts(posts)

    posts = add_comment_count(posts).order_by('-pub_date')
    page_obj = paginate_posts(request, posts)

    return render(request, 'blog/profile.html', {
        'profile': profile,
        'page_obj': page_obj
    })


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'blog/user.html'

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username})

    def get_object(self, queryset=None):
        """Возвращает текущего авторизованного пользователя"""
        return self.request.user


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username})


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(Post, pk=kwargs['post_id'])
        if self.object.author != request.user:
            return redirect('blog:detail', post_id=self.object.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blog:detail', kwargs={'post_id': self.object.pk})


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')
    pk_url_kwarg = 'post_id'
    form_class = PostForm

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not (
            request.user == self.object.author
            or request.user.is_superuser
        ):
            return redirect('blog:detail', post_id=self.object.pk)

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form_class(instance=self.object)
        return context


class PostsComment(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def get_post(self):
        return get_object_or_404(Post, pk=self.kwargs['post_id'])

    def form_valid(self, form):
        form.instance.post = self.get_post()
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:detail',
            kwargs={'post_id': self.kwargs['post_id']}) + '#comments'


class CommentBase(LoginRequiredMixin):
    """Базовый класс для работы с комментариями."""

    model = Comment
    pk_url_kwarg = 'comment_id'

    def get_success_url(self):
        comment = self.get_object()
        return reverse(
            'blog:detail', kwargs={'post_id': comment.post.pk}
        ) + '#comments'

    def get_queryset(self):
        """Пользователь может работать только со своими комментариями."""
        return self.model.objects.filter(author=self.request.user)


class CommentUpdate(CommentBase, UpdateView):
    template_name = 'blog/comment.html'
    form_class = CommentForm


class CommentDelete(CommentBase, DeleteView):
    template_name = 'blog/comment.html'
