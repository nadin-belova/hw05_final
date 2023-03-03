from django import forms
from .models import Post

from .models import Comment

# https://postimg.cc/LJ71v78k - скриншот дебагера


class PostForm(forms.ModelForm):
    class Meta:
        model = Post

        fields = ("text", "group", "image")

        labels = {
            "text": "Текст поста",
            "group": "Группа",
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Оставьте комментарий здесь...'}),
        }
