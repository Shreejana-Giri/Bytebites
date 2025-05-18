def get_dietary_status_message(user_profile):
    """Generate a personalized status message based on user profile data"""
    if not user_profile or not user_profile.bmi or not user_profile.daily_calories:
        return "Complete your profile to get personalized nutrition advice."
    
    messages = []
    
    # BMI status
    if user_profile.bmi < 18.5:
        messages.append("Your BMI indicates you're underweight. Focus on nutritious calorie-dense foods.")
    elif user_profile.bmi < 25:
        messages.append("Your BMI is in the healthy range. Keep up the good work!")
    elif user_profile.bmi < 30:
        messages.append("Your BMI indicates you're overweight. Focus on balanced nutrition and regular exercise.")
    else:
        messages.append("Your BMI indicates obesity. Consider consulting with a healthcare provider.")
    
    # Goal-specific message
    if user_profile.goal == 'maintain':
        messages.append(f"You're aiming to maintain your weight with {user_profile.daily_calories} calories daily.")
    elif user_profile.goal == 'lose':
        messages.append(f"You're on a weight loss journey with {user_profile.daily_calories} calories daily.")
    elif user_profile.goal == 'gain':
        messages.append(f"You're working on gaining weight with {user_profile.daily_calories} calories daily.")
    elif user_profile.goal == 'cut':
        messages.append(f"You're cutting with {user_profile.daily_calories} calories daily.")
    
    # Combine messages
    return " ".join(messages)

def calculate_health_metrics(weight, height, age, gender):
    """Calculate BMI and BMR from basic health data"""
    # Calculate BMI
    height_m = height / 100  # convert cm to m
    bmi = round(weight / (height_m ** 2), 2)
    
    # Calculate BMR using Mifflin-St Jeor Equation
    if gender == 'M':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    
    bmr = round(bmr, 2)
    
    return bmi, bmr
