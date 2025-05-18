from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .forms import (UserRegisterForm, UserProfileForm, LifestyleForm, 
                   GoalForm, ProgressRecordForm, FoodCalorieEstimationForm)
from .models import UserProfile, DietPlan, ProgressRecord, FoodCalorieEstimation
from .gemini_client import GeminiClient
import json
from django.conf import settings
import os
import base64
from .utils import get_dietary_status_message
from django.utils import timezone

def home(request):
    return render(request, 'nutrition/home.html')

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')

            UserProfile.objects.create(user=user)
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'nutrition/register.html', {'form': form})

@login_required
def profile(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        has_basic_info = all([
            user_profile.height, 
            user_profile.weight, 
            user_profile.age, 
            user_profile.gender
        ])
        has_lifestyle = bool(user_profile.lifestyle)
        has_goal = bool(user_profile.goal)
        
        bmi_category = None
        if user_profile.bmi:
            if user_profile.bmi < 18.5:
                bmi_category = "Underweight"
            elif user_profile.bmi < 25:
                bmi_category = "Normal weight"
            elif user_profile.bmi < 30:
                bmi_category = "Overweight"
            else:
                bmi_category = "Obese"
                
        
        latest_diet_plan = DietPlan.objects.filter(user=request.user).order_by('-date_generated').first()
        
        
        profile_status_message = get_dietary_status_message(user_profile)
        
        context = {
            'user_profile': user_profile,
            'has_basic_info': has_basic_info,
            'has_lifestyle': has_lifestyle,
            'has_goal': has_goal,
            'bmi_category': bmi_category,
            'latest_diet_plan': latest_diet_plan,
            'profile_status_message': profile_status_message
        }
        return render(request, 'nutrition/profile.html', context)
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=request.user)
        messages.info(request, "Let's set up your profile to get started!")
        return redirect('user_data')

@login_required
def user_data(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = UserProfile(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            user_profile = form.save(commit=False)
            
            user_profile.calculate_bmi()
            user_profile.calculate_bmr()
            user_profile.save()
            
            messages.success(request, "Personal information updated successfully!")
            
            if user_profile.lifestyle:
                return redirect('goals')
            else:
                return redirect('lifestyle')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'nutrition/user_data.html', {'form': form})

@login_required
def lifestyle(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
        messages.info(request, "Your profile has been created. Please complete your personal information first.")
        return redirect('user_data')
    
    if request.method == 'POST':
        form = LifestyleForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Lifestyle information updated successfully!")
            return redirect('goals')
    else:
        form = LifestyleForm(instance=profile)
    
    return render(request, 'nutrition/lifestyle.html', {'form': form})

@login_required
def goals(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
        messages.info(request, "Your profile has been created. Please complete your personal information first.")
        return redirect('user_data')
    
    if not profile.height or not profile.weight or not profile.age or not profile.gender:
        messages.warning(request, "Please complete your basic information before setting goals.")
        return redirect('user_data')
        
    if not profile.lifestyle:
        messages.warning(request, "Please select your lifestyle before setting goals.")
        return redirect('lifestyle')
    
    if request.method == 'POST':
        form = GoalForm(request.POST, instance=profile)
        if form.is_valid():
            user_profile = form.save(commit=False)
            
            # Calculate daily calories
            user_profile.calculate_daily_calories()
            user_profile.save()
            
            messages.success(request, "Goals updated successfully!")
            return redirect('diet_plan')
    else:
        form = GoalForm(instance=profile)
    
    return render(request, 'nutrition/goals.html', {'form': form})

@login_required
def diet_plan(request):
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        
        messages.info(request, "Please set up your profile to get started.")
        return redirect('user_data') 

    required_fields = [
        profile.height, profile.weight, profile.age, profile.gender,
        profile.lifestyle, profile.goal, profile.diet_preference
    ]
    if not all(required_fields):
        messages.warning(request, "Your profile is incomplete. Please update all required fields (personal info, lifestyle, goal, diet preference) to generate a diet plan.")
        return redirect('profile') 

  
    if not profile.bmi:
        profile.calculate_bmi()
    if not profile.bmr:
        profile.calculate_bmr()
    if not profile.daily_calories:
        profile.calculate_daily_calories()
   
    if not all([profile.bmi, profile.bmr, profile.daily_calories]):
        profile.save() 

    latest_plan = DietPlan.objects.filter(user=request.user).order_by('-date_generated').first()
    error_message = None 

    if request.method == 'POST': 
        if not settings.GEMINI_API_KEY:
            messages.error(request, "Gemini API key is not configured. Please contact the administrator.")
            
            error_message = "Gemini API key is not configured. Cannot generate plan."
            return render(request, 'nutrition/diet_plan.html', {
                'profile': profile,
                'diet_plan': latest_plan, 
                'error': error_message
            })

        try:
            gemini_client = GeminiClient(api_key=settings.GEMINI_API_KEY, model_name=settings.GEMINI_MODEL)

            prompt = f"""
            Generate a personalized daily diet plan for a user with the following characteristics:
            - Age: {profile.age} years
            - Gender: {profile.get_gender_display()}
            - Height: {profile.height} cm
            - Weight: {profile.weight} kg
            - BMI: {profile.bmi:.2f}
            - BMR (Basal Metabolic Rate): {profile.bmr:.0f} calories
            - Estimated Daily Calorie Target: {profile.daily_calories:.0f} calories
            - Diet Preference: {profile.get_diet_preference_display()}
            - Lifestyle: {profile.get_lifestyle_display()}
            - Fitness Goal: {profile.get_goal_display()}
            - Allergies or Disliked Foods: {profile.allergies if profile.allergies else 'None specified'}
            - make sure the diet is in nepali style as this is tailored made for nepali people

            The diet plan should strictly adhere to the Daily Calorie Target of {profile.daily_calories:.0f} calories.
            
            Please provide in such format:
            1.  A summary section stating the "Estimated Daily Calorie Target: {profile.daily_calories:.0f} calories".
            2.  Detailed meal suggestions for:
                *   Breakfast
                *   Mid-Morning Snack
                *   Lunch
                *   Afternoon Snack
                *   Dinner
            3.  For each meal and snack:
                *   List specific food items.
                *   Provide estimated portion sizes (e.g., grams, cups, pieces).
                *   Provide an approximate calorie count for that meal/snack.
                *   Provide an approximate macronutrient breakdown (Protein, Carbohydrates, Fat in grams) for that meal/snack.
            4.  Ensure the sum of calories for all meals and snacks is very close to {profile.daily_calories:.0f} calories.
            5.  The entire plan must respect the user's Diet Preference (e.g., {profile.get_diet_preference_display()}).
            6.  The plan must avoid any items listed under "Allergies or Disliked Foods".
            7.  Offer healthy food choices and promote variety.
            8.  Consider providing 1-2 alternative options for each main meal (Breakfast, Lunch, Dinner) that are nutritionally similar and adhere to the same calorie and dietary constraints.

            Format the output clearly using Markdown. Use headings for sections (e.g., ## Breakfast, ### Alternatives). Use bullet points for food items.

            Example for a meal:
            ## Breakfast (Approx. XXX Calories - P: Xg, C: Yg, F: Zg)
            *   Food Item 1 (e.g., Oatmeal, 1 cup cooked)
            *   Food Item 2 (e.g., Berries, 1/2 cup)
            *   Food Item 3 (e.g., Almonds, 10-12)
            ### Alternatives
            *   Alternative Food Item 1...

            Start the entire response with the calorie target summary.
            """

           
            generated_text = gemini_client.generate_text(prompt)
           

            
            parsed_daily_calories = profile.daily_calories 
            try:
                for line in generated_text.split('\n'):
                    if "estimated daily calorie target:" in line.lower():
                       
                        import re
                        match = re.search(r'(\d+)\s*calories', line.lower())
                        if match:
                            parsed_daily_calories = int(match.group(1))
                            break
            except Exception as e:
                print(f"Could not parse calories from Gemini response: {e}")
               

           
            if latest_plan: 
                latest_plan.diet_plan = generated_text 
                latest_plan.daily_calories = parsed_daily_calories
                latest_plan.date_generated = timezone.now()
                latest_plan.save()
            else: 
                latest_plan = DietPlan.objects.create(
                    user=request.user,
                    diet_plan=generated_text, 
                    daily_calories=parsed_daily_calories,
                    date_generated=timezone.now()
                )
            
            messages.success(request, "New diet plan generated successfully!")
            return redirect('diet_plan')

        except Exception as e:
            
            error_message = f"An error occurred while generating the diet plan: {str(e)}"
            messages.error(request, error_message)
            print(f"Error in diet_plan generation: {e}") 

    
    return render(request, 'nutrition/diet_plan.html', {
        'profile': profile,
        'diet_plan': latest_plan,
        'error': error_message 
    })

def aboutus(request):
    return render(request, 'nutrition/aboutus.html')

def how_it_works(request):
    return render(request, 'nutrition/how-it-works.html')

