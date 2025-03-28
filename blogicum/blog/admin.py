# Register your models here.
from django.contrib import admin
from .models import Post, Location, Category, Comment
from django.contrib.auth.admin import UserAdmin


class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'description', 'is_published', 'slug', 'created_at')
    list_editable = ('is_published')
    list_filter = ('is_published', 'created_at')
    search_fields = ('title')


class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_published', 'created_at')
    list_editable = ('is_published',)
    list_filter = ('is_published', 'created_at')
    search_fields = ('name',)


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'text',
        'pub_date',
        'author',
        'category',
        'location',
        'is_published',
        'created_at',
        'image',
    )
    list_editable = ('is_published',)
    list_filter = (
        'is_published',
        'category',
        'location',
        'pub_date',
        'created_at'
    )
    search_fields = ('title', 'text')


class CommentAdmin(admin.ModelAdmin):
    list_display = ('text', 'author', 'post', 'created')
    list_filter = ('created', 'author')
    search_fields = ('text')


class CustomUserAdmin(UserAdmin):
    list_display = (
        'username',
        'email',
        'password'
        'first_name',
        'last_name'
    )


admin.site.register(Post, PostAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Comment, CommentAdmin)
