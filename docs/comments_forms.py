from django import forms
from .models import Comment, Rating, Favorite


class CommentForm(forms.ModelForm):
    """Форма для добавления комментария"""
    parent = forms.IntegerField(
        widget=forms.HiddenInput,
        required=False
    )

    class Meta:
        model = Comment
        fields = ['content', 'parent']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Напишите ваш комментарий...',
                'maxlength': '1000'
            }),
        }
        labels = {
            'content': 'Текст комментария'
        }

    def clean_content(self):
        content = self.cleaned_data.get('content')
        if not content or len(content.strip()) == 0:
            raise forms.ValidationError('Комментарий не может быть пустым')
        if len(content) > 1000:
            raise forms.ValidationError('Комментарий не может превышать 1000 символов')
        return content.strip()


class CommentEditForm(forms.ModelForm):
    """Форма для редактирования комментария"""

    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Редактируйте ваш комментарий...',
                'maxlength': '1000'
            }),
        }
        labels = {
            'content': 'Текст комментария'
        }

    def clean_content(self):
        content = self.cleaned_data.get('content')
        if not content or len(content.strip()) == 0:
            raise forms.ValidationError('Комментарий не может быть пустым')
        if len(content) > 1000:
            raise forms.ValidationError('Комментарий не может превышать 1000 символов')
        return content.strip()