from django.contrib import admin
from .models import Post, Category, Tag, Comment, Profile
#from ckeditor.widgets import CKEditorWidget

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title','category','published','created']
    list_filter = ['published','category']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title','content']

admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(Comment)
admin.site.register(Profile)