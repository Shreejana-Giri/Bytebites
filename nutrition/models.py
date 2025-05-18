from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    height = models.FloatField(help_text="Height in cm", null=True, blank=True)
    weight = models.FloatField(help_text="Weight in kg", null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=[('M', 'Male'), ('F', 'Female')], null=True, blank=True)
    diet_preference = models.CharField(max_length=10, choices=[('veg', 'Vegetarian'), ('non-veg', 'Non-Vegetarian')], null=True, blank=True)
    allergies = models.TextField(null=True, blank=True)
    lifestyle = models.CharField(
        max_length=20, 
        choices=[
            ('sedentary', 'Sedentary'),
            ('lightly_active', 'Lightly Active'),
            ('moderately_active', 'Moderately Active'),
            ('very_active', 'Very Active'),
            ('athletic', 'Athletic')
        ],
        null=True, 
        blank=True
    )
    goal = models.CharField(
        max_length=10,
        choices=[
            ('maintain', 'Maintain'),
            ('lose', 'Lose'),
            ('gain', 'Gain'),
            ('cut', 'Cut')
        ],
        null=True,
        blank=True
    )
    bmr = models.FloatField(null=True, blank=True)
    bmi = models.FloatField(null=True, blank=True)
    daily_calories = models.FloatField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def calculate_bmi(self):
        if self.height and self.weight:
            height_m = self.height / 100  # convert cm to m
            self.bmi = round(self.weight / (height_m ** 2), 2)
            return self.bmi
        return None
    
    def calculate_bmr(self):
        if self.weight and self.height and self.age and self.gender:
            if self.gender == 'M':
                # for men
                self.bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age + 5
            else:
                #  women
                self.bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age - 161
            return round(self.bmr, 2)
        return None
    
    def calculate_daily_calories(self):
        if self.bmr and self.lifestyle:
            # Activity multipliers
            activity_multipliers = {
                'sedentary': 1.2,
                'lightly_active': 1.375,
                'moderately_active': 1.55,
                'very_active': 1.725,
                'athletic': 1.9
            }
            
            # Calculate TDEE (Total Daily Energy Expenditure)
            tdee = self.bmr * activity_multipliers.get(self.lifestyle, 1.2)
            
            # Adjust based on goals
            goal_adjustments = {
                'maintain': 0,
                'lose': -500,  
                'gain': 500,   
                'cut': -250    
            }
            
            self.daily_calories = round(tdee + goal_adjustments.get(self.goal, 0), 0)
            return self.daily_calories
        return None

class DietPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date_generated = models.DateTimeField(default=timezone.now)
    daily_calories = models.FloatField()
    diet_plan = models.TextField()
    alternatives = models.TextField()
    
    def __str__(self):
        return f"{self.user.username}'s Diet Plan - {self.date_generated.date()}"

class ProgressRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    weight = models.FloatField(help_text="Weight in kg")
    calories_consumed = models.IntegerField(help_text="Total calories consumed today", null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Progress - {self.date}"
    
    class Meta:
        ordering = ['-date']

class FoodCalorieEstimation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(default=timezone.now)
    food_image = models.ImageField(upload_to='food_images/')
    description = models.TextField(help_text="Description of the food and ingredients")
    portion = models.CharField(max_length=100, help_text="Portion size", null=True, blank=True)
    estimated_calories = models.IntegerField(null=True, blank=True)
    nutrition_details = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Food - {self.date}"
    
    class Meta:
        ordering = ['-date']
