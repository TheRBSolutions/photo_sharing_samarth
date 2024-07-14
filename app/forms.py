# gallery/forms.py
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Album, Business, Media, Profile, UserProfile



class CreateUserForm(UserCreationForm):
    email = forms.EmailField(required=True)
    is_photographer = forms.BooleanField(required=False, label='Sign up as Photographer')

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2", "is_photographer"]

    def save(self, commit=True):
        user = super(CreateUserForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            profile = Profile(user=user, is_photographer=self.cleaned_data["is_photographer"])
            profile.save()
        return user
    
# class CreateUserForm(UserCreationForm):
#     class Meta:
#         model = User
#         fields = ["username", "email", "password1", "password2"]

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['email', 'selfie']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'selfie': forms.FileInput(attrs={'class': 'form-control'}),
        }
            
class MediaForm(forms.ModelForm):
    class Meta:
        model = Media
        fields = ['file']
        
    # file = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
        
class AlbumForm(forms.ModelForm):
    class Meta:
        model = Album
        fields = ['title', 'description', 'cover_image']


class PhotographerSettingsForm(forms.ModelForm):
    username = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    # is_photographer = forms.BooleanField(required=False, label='Sign up as Photographer')
    password1 = forms.CharField(widget=forms.PasswordInput, required=False, label='Password')
    password2 = forms.CharField(widget=forms.PasswordInput, required=False, label='Confirm Password')

    class Meta:
        model = Profile
        fields = ["username", "email",  "password1", "password2"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(PhotographerSettingsForm, self).__init__(*args, **kwargs)
        self.fields['username'].initial = user.username
        self.fields['email'].initial = user.email
        
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password1 != password2:
            raise forms.ValidationError("Passwords do not match")

        return cleaned_data

    def save(self, commit=True):
        profile = super(PhotographerSettingsForm, self).save(commit=False)
        user = profile.user
        user.email = self.cleaned_data["email"]
        user.username = self.cleaned_data["username"]

        password = self.cleaned_data.get('password1')
        if password:
            user.set_password(password)

        if commit:
            user.save()
            profile.save()
        return profile
    
class BusinessSettingsForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = ['name', 'phone_number', 'email', 'website', 'social_media_links', 'logo']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'social_media_links': forms.Textarea(attrs={'class': 'form-control'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }