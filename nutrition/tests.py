from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import UserProfile

class NutritionAppTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        
        # Create user profile
        self.profile = UserProfile.objects.create(
            user=self.user,
            height=180,
            weight=80,
            age=30,
            gender='M',
            diet_preference='non-veg',
            lifestyle='moderately_active',
            goal='maintain'
        )
    
    def test_bmi_calculation(self):
        """Test BMI calculation"""
        bmi = self.profile.calculate_bmi()
        self.assertAlmostEqual(bmi, 24.69, places=2)
    
    def test_bmr_calculation(self):
        """Test BMR calculation"""
        bmr = self.profile.calculate_bmr()
        self.assertAlmostEqual(bmr, 1780.0, places=2)
    
    def test_daily_calories_calculation(self):
        """Test daily calories calculation"""
        self.profile.bmr = 1780.0
        daily_calories = self.profile.calculate_daily_calories()
        self.assertAlmostEqual(daily_calories, 2759.0, places=0)
    
    def test_home_page(self):
        """Test that home page loads correctly"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
    
    def test_login_required(self):
        """Test that protected pages require login"""
        response = self.client.get(reverse('profile'))
        self.assertNotEqual(response.status_code, 200)
        
        # Now login and try again
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
