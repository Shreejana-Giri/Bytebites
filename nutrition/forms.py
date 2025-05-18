from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, ProgressRecord, FoodCalorieEstimation

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class UserProfileForm(forms.ModelForm):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    
    DIET_PREFERENCE_CHOICES = [
        ('veg', 'Vegetarian'),
        ('non-veg', 'Non-Vegetarian'),
    ]
    
    gender = forms.ChoiceField(choices=GENDER_CHOICES, widget=forms.RadioSelect)
    diet_preference = forms.ChoiceField(choices=DIET_PREFERENCE_CHOICES, widget=forms.RadioSelect)
    allergies = forms.CharField(widget=forms.Textarea, required=False)
    
    class Meta:
        model = UserProfile
        fields = ['height', 'weight', 'age', 'gender', 'diet_preference', 'allergies']

class LifestyleForm(forms.ModelForm):
    LIFESTYLE_CHOICES = [
        ('sedentary', 'Sedentary (little or no exercise)'),
        ('lightly_active', 'Lightly Active (light exercise/sports 1-3 days/week)'),
        ('moderately_active', 'Moderately Active (moderate exercise/sports 3-5 days/week)'),
        ('very_active', 'Very Active (hard exercise/sports 6-7 days a week)'),
        ('athletic', 'Athletic (very hard exercise, training, or physical job)')
    ]
    
    lifestyle = forms.ChoiceField(choices=LIFESTYLE_CHOICES, widget=forms.RadioSelect)
    
    class Meta:
        model = UserProfile
        fields = ['lifestyle']

class GoalForm(forms.ModelForm):
    GOAL_CHOICES = [
        ('maintain', 'Maintain current weight'),
        ('lose', 'Lose weight'),
        ('gain', 'Gain weight/bulk up'),
        ('cut', 'Cut (lose fat while preserving muscle)')
    ]
    
    goal = forms.ChoiceField(choices=GOAL_CHOICES, widget=forms.RadioSelect)
    
    class Meta:
        model = UserProfile
        fields = ['goal']

class ProgressRecordForm(forms.ModelForm):
    class Meta:
        model = ProgressRecord
        fields = ['weight', 'calories_consumed', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class FoodCalorieEstimationForm(forms.ModelForm):
    class Meta:
        model = FoodCalorieEstimation
        fields = ['food_image', 'description', 'portion']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Describe the ingredients used in your meal'}),
            'portion': forms.TextInput(attrs={'placeholder': 'e.g., 1 cup, 200g, 1 serving'})
        }
