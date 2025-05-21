import json
import google.generativeai as genai
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.conf import settings
from enum import Enum
from django.contrib.auth.models import AnonymousUser

# --- Enum Definitions ---
class Gender(str, Enum):
    male = "male"
    female = "female"

class ActivityLevel(str, Enum):
    sedentary = "Sedentary (little or no exercise)"
    lightly_active = "Lightly active (light exercise/sports 1-3 days/week)"
    moderately_active = "Moderately active (moderate exercise/sports 3-5 days/week)"
    very_active = "Very active (hard exercise/sports 6-7 days a week)"
    extra_active = "Extra active (very hard exercise/sports & physical job or 2x training)"

# --- Health Metrics Calculation Functions ---
def calculate_bmi(weight_kg: float, height_cm: float) -> float | None:
    if height_cm <= 0:
        return None
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    return round(bmi, 2)

def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: Gender) -> float | None:
    """Calculates BMR using the Mifflin-St Jeor Equation."""
    if gender == Gender.male:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    elif gender == Gender.female:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
    else:
        return None
    return round(bmr, 2)

def calculate_tdee(bmr: float, activity_level: ActivityLevel) -> float | None:
    """Calculates TDEE based on BMR and activity level."""
    if bmr is None:
        return None
    activity_multipliers = {
        ActivityLevel.sedentary: 1.2,
        ActivityLevel.lightly_active: 1.375,
        ActivityLevel.moderately_active: 1.55,
        ActivityLevel.very_active: 1.725,
        ActivityLevel.extra_active: 1.9
    }
    multiplier = activity_multipliers.get(activity_level)
    if multiplier is None:
        return None
    return round(bmr * multiplier, 2)

# --- System Prompt for LLM ---
MAX_HISTORY_TURNS = 3  # Number of recent user/assistant turn pairs to include in the prompt

SYSTEM_PROMPT_TEMPLATE = """You are a friendly, encouraging, and expert Nepali Nutrition & Wellness Assistant.
Your primary goal is to help users with their nutrition, diet plans, and promote a healthy lifestyle with a strong focus on Nepali cuisine and culture.
Your tone should be positive, supportive, and natural, like a knowledgeable friend. Your responses should be very concise, like short chat messages. Aim for 1-3 sentences per turn unless providing a list or steps.

Chat History (Recent Turns):
{chat_history}

Strict Limitations & Guidelines:
1.  Scope: You MUST ONLY answer questions directly related to nutrition, food (especially Nepali food), diet plans, recipes, healthy eating habits, general fitness advice related to diet, and motivation for a healthy lifestyle.
2.  Off-Topic Questions: If the user asks about any other topic, you MUST politely decline. Gently guide them back: "I'm geared up to help with your nutrition and wellness journey! That topic is a bit outside my kitchen, but ask me anything about healthy Nepali meals or fitness motivation! 😊"
3.  Medical Advice: Do NOT provide specific medical advice. You can provide general nutritional information.
4.  Nepali Food Promotion: When suggesting foods or meals, ALWAYS prioritize and enthusiastically recommend locally available and traditional Nepali food items. Briefly explain their benefits. (e.g., "How about some rich and warming Gundruk ko Jhol? It's great for digestion!")
5.  Motivational Support: Weave in short, natural, and encouraging words or positive affirmations. (e.g., "You've got this!", "Every healthy choice is a step forward. 👍")
6.  Answering in Installments for Complex Queries:
    *   For any question that needs a longer answer (detailed diet plan, long recipe, multi-step explanation), give only the FIRST part or a very brief summary.
    *   Then, explicitly ask if the user wants to hear the next part or more details. (e.g., "That's the gist of it. Want to dive into the details?" or "First step is X. Ready for step two?")
    *   Wait for the user's confirmation before providing subsequent installments.
7.  Recipe Sharing (Installment Style): If asked for recipes: Ingredients and first 1-2 steps. Then ask, "Shall I continue with the cooking steps? 👨‍🍳"
8.  Diet Plans (Installment Style): If a diet plan is requested:
    *   With profile (TDEE available): Suggest a target calorie range/goal. Then ask, "Would you like a sample breakfast idea for that? 🍳" or "Want a sample meal outline for one day?"
    *   Without profile: Give a very general tip. Then warmly encourage profile completion: "For example, adding more colorful local veggies is always a win! 🥦 For a plan more tailored to you, filling out your profile in the sidebar with your age, height, etc., would be really helpful so I can give you the best suggestions! Want to do that quickly?"
9.  Clarity, Simplicity, and Engagement:
    *   Provide easy-to-understand answers. Be direct yet friendly. Avoid long paragraphs.
    *   Use relevant emojis sparingly (🌿, 👍, 😊, 👨‍🍳, 🍳, 🥦) to add a touch of warmth and personality. Don't overdo it.
    *   Occasionally, after giving information, ask a gentle, related follow-up question to encourage interaction or check understanding, like "Does that make sense?" or "What are your thoughts on that?" or "Anything specific about that you're curious about?"
    *   Start responses with varied, natural acknowledgements like "Okay!", "Sure thing!", "Got it.", "Great question!", "Let's see..."

User Profile Information:
{user_profile_details}

Based on all the above (including chat history if relevant), please answer the user's current question. Remember: be concise, natural, conversational, and use installments for longer answers, always checking if the user wants to proceed.
User Question: {user_question}
Answer:"""

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.chat_history = []

        # Initialize Gemini AI
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

            # Send welcome message
            await self.send(text_data=json.dumps({
                'message': "Welcome to the Nepali Nutrition & Wellness Assistant! How can I help you today?",
                'sender': 'assistant'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'message': f"Error initializing AI: {str(e)}",
                'sender': 'system'
            }))

    async def disconnect(self, close_code):
        pass

    @database_sync_to_async
    def get_user_profile(self, user):
        """Get user profile information from the database"""
        try:
            from .models import UserProfile
            profile = UserProfile.objects.get(user=user)

            # Format profile details similar to the streamlit version
            details = [
                f"Name: {user.username}",
                f"Age: {profile.age} years",
                f"Height: {profile.height} cm",
                f"Weight: {profile.weight} kg",
                f"Gender: {'Male' if profile.gender == 'M' else 'Female'}",
            ]

            # Add BMI, BMR, and TDEE if available
            if profile.bmi:
                details.append(f"BMI: {profile.bmi}")
            if profile.bmr:
                details.append(f"Calculated BMR: {profile.bmr} kcal/day")
            if profile.daily_calories:
                details.append(f"Estimated TDEE for diet planning: {profile.daily_calories} kcal/day")

            return "Current user profile:\n- " + "\n- ".join(details)
        except Exception as e:
            return f"User is logged in but profile information could not be retrieved. Error: {str(e)}"

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Add user message to chat history
        self.chat_history.append({"role": "user", "content": message})

        # Get user profile if available
        user_profile_details_string = "No profile information provided by the user yet."

        # If user is authenticated, try to get their profile
        if self.scope["user"] and not isinstance(self.scope["user"], AnonymousUser):
            user_profile_details_string = await self.get_user_profile(self.scope["user"])

        # Format chat history
        chat_history_string = "No previous conversation turns in this session yet."
        relevant_messages = self.chat_history[-(MAX_HISTORY_TURNS * 2):-1]  # Get up to last N turns, excluding current user input

        if relevant_messages:
            formatted_history = []
            for msg in relevant_messages:
                role = "User" if msg["role"] == "user" else "Assistant"
                formatted_history.append(f"{role}: {msg['content']}")
            chat_history_string = "\n".join(formatted_history)

        # Construct the prompt for the LLM
        final_llm_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            chat_history=chat_history_string,
            user_profile_details=user_profile_details_string,
            user_question=message
        )

        try:
            # Generate response from LLM
            response = self.model.generate_content(final_llm_prompt)
            assistant_response = response.text

            # Add assistant response to chat history
            self.chat_history.append({"role": "assistant", "content": assistant_response})

            # Send response back to the client
            await self.send(text_data=json.dumps({
                'message': assistant_response,
                'sender': 'assistant'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'message': f"Sorry, I encountered an error while trying to respond. Please try again. Error: {str(e)}",
                'sender': 'system'
            }))
