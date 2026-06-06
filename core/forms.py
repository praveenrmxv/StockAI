from django import forms
from .models import Product
from .models import Profile


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'quantity', 'price']


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image']