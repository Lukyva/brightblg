from django import forms
from .models import Comment
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CommentForm(forms.ModelForm):
    parent_id = forms.IntegerField(widget=forms.HiddenInput, required=False) # ADD THIS

    class Meta:
        model = Comment
        fields = ['body', 'parent_id']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Write a comment...', 'class': 'comment-textarea'}),
        }
        labels = {'body': ''}
       
class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
        