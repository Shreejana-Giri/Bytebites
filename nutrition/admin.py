from django.contrib import admin
from .models import UserProfile, DietPlan, ProgressRecord, FoodCalorieEstimation

# Register the models for the admin interface
admin.site.register(UserProfile)
admin.site.register(DietPlan)
admin.site.register(ProgressRecord)
admin.site.register(FoodCalorieEstimation)
