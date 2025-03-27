from django.views.generic import (
    ListView,
    DetailView,
    detail,
    FormView,
    UpdateView,
    DeleteView)
from .models import Post, Category, Comment
from django.utils import timezone
from django.http import Http404
from django.db.models import Count
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import CommentForm, UserProfileForm
from django.core.paginator import Paginator
# Create your views here.


class PostListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'post_list'
    ordering = 'id'
    paginate_by = 10

    def get_queryset(self):
        return Post.objects.filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True
        ).annotate(
            comment_count=Count('comment')
        ).order_by('-pub_date')


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
        return Post.objects.filter(
            category=self.category,
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True
        ).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'category': self.category,
            'total_posts': self.get_queryset().count()
        })
        return context


class PostDetailView(DetailView):
    model = Post
    ordering = 'id'
    template_name = 'blog/detail.html'

    def get_object(self, queryset=None):
        post = get_object_or_404(Post, pk=self.kwargs['pk'])

        if not (post.is_published and post.category.is_published
                and post.pub_date <= timezone.now()):
            # Если пост не опубликован, проверяем авторство
            if self.request.user != post.author:
                raise Http404("Запись не найдена или не опубликована")

        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comment_set.all().order_by('created')
        context['form'] = CommentForm()
        return context


def profile_view(request, username):
    profile = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=profile).annotate(
        comment_count=Count('comment')
    ).order_by('-pub_date')

    if request.user != profile:
        posts = posts.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
        )
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'profile': profile,
        'page_obj': page_obj   # posts
    }
    return render(request, 'blog/profile.html', context)


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
    fields = ['title', 'text', 'pub_date', 'location', 'category', 'image']
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
    fields = ['title', 'text', 'pub_date', 'location', 'category', 'image']
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.author != request.user:
            return redirect('blog:detail', pk=self.object.pk)

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blog:detail', kwargs={'pk': self.object.pk})


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not (
            request.user == self.object.author
            or request.user.is_superuser
        ):
            return redirect('blog:detail', pk=self.object.pk)

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Перед удалением можно добавить логику проверки
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post'] = self.get_object()
        return context


class PostsComment(
        LoginRequiredMixin,
        detail.SingleObjectMixin,
        FormView
):
    model = Post
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        comment = form.save(commit=False)
        comment.post = self.object
        comment.author = self.request.user
        comment.save()
        return super().form_valid(form)

    def get_success_url(self):
        post = self.get_object()
        return reverse('blog:detail', kwargs={'pk': post.pk}) + '#comments'


class CommentBase(LoginRequiredMixin):
    """Базовый класс для работы с комментариями."""

    model = Comment

    def get_success_url(self):
        comment = self.get_object()
        return reverse(
            'blog:detail', kwargs={'pk': comment.post.pk}
        ) + '#comments'

    def get_queryset(self):
        """Пользователь может работать только со своими комментариями."""
        return self.model.objects.filter(author=self.request.user)


class CommentUpdate(CommentBase, UpdateView):
    """Редактирование комментария."""

    template_name = 'blog/comment.html'
    form_class = CommentForm


class CommentDelete(CommentBase, DeleteView):
    """Удаление комментария."""

    template_name = 'blog/comment.html'
