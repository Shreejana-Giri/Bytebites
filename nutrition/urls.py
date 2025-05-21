from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='nutrition/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('user_data/', views.user_data, name='user_data'),
    path('lifestyle/', views.lifestyle, name='lifestyle'),
    path('goals/', views.goals, name='goals'),
    path('diet_plan/', views.diet_plan, name='diet_plan'),
    path('aboutus/', views.aboutus, name='aboutus'),
    path('how-it-works/', views.how_it_works, name='how_it_works'),
]
