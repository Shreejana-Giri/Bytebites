import streamlit as st
st.set_page_config(page_title="Nepali Nutrition & Wellness Assistant", page_icon="🌿")
import google.generativeai as genai
# numpy is no longer needed as cosine_similarity is removed
from pydantic import BaseModel, ValidationError, Field, field_validator # For data validation
from enum import Enum # For Gender options


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

# --- User Profile Model (Pydantic) ---
class UserProfile(BaseModel):
    name: str = Field(..., min_length=1, description="User's full name.")
    age: int = Field(..., gt=0, le=120, description="User's age in years.")
    height_cm: float = Field(..., gt=0, le=300, description="User's height in centimeters.")
    weight_kg: float = Field(..., gt=0, le=500, description="User's weight in kilograms.")
    gender: Gender = Field(..., description="User's gender.")
    activity_level: ActivityLevel = Field(..., description="User's typical activity level.")

    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, value):
        if not value.strip():
            raise ValueError('Name cannot be empty.')
        return value.strip()

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

# --- Configuration ---
GOOGLE_API_KEY = "AIzaSyD2JrW72oo2aRwOIhDNNgoQ7FSNfv67lRQ" # User provided API Key

try:
    genai.configure(api_key=GOOGLE_API_KEY)
    # Initialize the generative model (ensure this is the correct model name you intend to use)
    model = genai.GenerativeModel('gemini-2.5-flash-preview-04-17')
    # embedding_model is no longer needed
    # st.success("Google API Key configured successfully! LLM is ready.") # Commented out as per user request
except Exception as e:
    st.error(f"Error configuring Google API: {e}")
    st.stop()

# --- App Title ---
st.title("🌿 Nepali Nutrition & Wellness Assistant")
st.write("""
Welcome! I am your personal wellness companion focused on nutrition and health, 
especially tailored for Nepali users.
""")
st.info("Note: This chatbot now uses its general knowledge, guided to focus on Nepali nutrition and wellness.")

# --- User Profile Input in Sidebar (remains the same) ---
st.sidebar.header("👤 Your Profile")
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = None
if 'profile_errors' not in st.session_state:
    st.session_state.profile_errors = {}

if st.session_state.user_profile:
    profile = st.session_state.user_profile
    st.sidebar.success("Profile Loaded!")
    st.sidebar.markdown(f"Name: {profile.name}")
    st.sidebar.markdown(f"Age: {profile.age} years")
    st.sidebar.markdown(f"Height: {profile.height_cm} cm")
    st.sidebar.markdown(f"Weight: {profile.weight_kg} kg")
    st.sidebar.markdown(f"Gender: {profile.gender.value.title()}")
    st.sidebar.markdown(f"Activity Level: {profile.activity_level.value}")
    bmi = calculate_bmi(profile.weight_kg, profile.height_cm)
    bmr = calculate_bmr(profile.weight_kg, profile.height_cm, profile.age, profile.gender)
    tdee = calculate_tdee(bmr, profile.activity_level) if bmr is not None else None
    if bmi is not None: st.sidebar.markdown(f"BMI: {bmi}")
    if bmr is not None: st.sidebar.markdown(f"BMR (Mifflin-St Jeor): {bmr} kcal/day")
    if tdee is not None: st.sidebar.markdown(f"Est. TDEE: {tdee} kcal/day")
    
    if st.sidebar.button("Clear Profile and Edit"):
        st.session_state.user_profile = None
        st.session_state.profile_errors = {}
        st.rerun()
else: # If no profile is loaded, show the form to create/edit profile
    st.sidebar.markdown("### Create Your Profile")
    with st.sidebar.form(key="profile_form", clear_on_submit=False):
        st.write("Please enter your details below:")
        
        default_profile = st.session_state.user_profile # This will be None here, so fields start empty or with hardcoded defaults
        name_input = st.text_input("Name", value="") # Start empty
        age_input = st.number_input("Age (years)", min_value=1, max_value=120, value=25, step=1) # Default to 25
        height_input = st.number_input("Height (cm)", min_value=1.0, max_value=300.0, value=160.0, step=0.1, format="%.1f") # Default
        weight_input = st.number_input("Weight (kg)", min_value=1.0, max_value=500.0, value=60.0, step=0.1, format="%.1f") # Default
        gender_input = st.radio("Gender", options=[g.value for g in Gender], index=0, format_func=lambda x: x.title()) # Default to first option
        activity_level_input = st.selectbox("Activity Level", options=[level.value for level in ActivityLevel], index=2) # Default to moderately active
        
        submit_button = st.form_submit_button(label="Save Profile")

        if submit_button:
            st.session_state.profile_errors = {} # Clear previous errors on new submission
            try:
                user_data = {"name": name_input, "age": int(age_input), "height_cm": float(height_input), "weight_kg": float(weight_input), "gender": gender_input, "activity_level": activity_level_input}
                validated_profile = UserProfile(**user_data)
                st.session_state.user_profile = validated_profile
                st.sidebar.success("Profile saved successfully!")
                st.rerun() # Rerun to display the loaded profile and hide the form
            except ValidationError as e:
                for error in e.errors():
                    field_name = error['loc'][0]
                    error_msg = error['msg']
                    st.session_state.profile_errors[field_name] = error_msg
                    # Errors are now displayed below the form if it re-renders due to an error
            except ValueError as ve:
                st.sidebar.error(f"Invalid input: Please ensure all fields are correctly filled. {ve}")

    # Display Pydantic validation errors below the form if they occurred
    # These will only show if the form submission failed and the page rerendered with the form still visible.
    if st.session_state.profile_errors: 
        for field, msg in st.session_state.profile_errors.items():
             st.sidebar.error(f"Error in {field.replace('cm',' (cm)').replace('_kg',' (kg)').replace('',' ').title()}: {msg}")
        # It's good to clear them after displaying if the form is re-submitted, 
        # but the current logic inside the form already clears errors at the start of a new submission.


# --- System Prompt for LLM ---
MAX_HISTORY_TURNS = 3 # Number of recent user/assistant turn pairs to include in the prompt

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

# --- Chat Interface ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input_prompt := st.chat_input("What would you like to know about Nepali nutrition and wellness?"):
    st.session_state.messages.append({"role": "user", "content": user_input_prompt})
    with st.chat_message("user"):
        st.markdown(user_input_prompt)

    with st.chat_message("assistant"):
        user_profile_details_string = "No profile information provided by the user yet."
        if st.session_state.user_profile:
            profile = st.session_state.user_profile
            bmi = calculate_bmi(profile.weight_kg, profile.height_cm)
            bmr = calculate_bmr(profile.weight_kg, profile.height_cm, profile.age, profile.gender)
            tdee = calculate_tdee(bmr, profile.activity_level) if bmr is not None else None
            details = [
                f"Name: {profile.name}",
                f"Age: {profile.age} years",
                f"Height: {profile.height_cm} cm",
                f"Weight: {profile.weight_kg} kg",
                f"Gender: {profile.gender.value.title()}",
                f"Activity Level: {profile.activity_level.value}"
            ]
            if bmi: details.append(f"BMI: {bmi}")
            if bmr: details.append(f"Calculated BMR: {bmr} kcal/day")
            if tdee: details.append(f"Estimated TDEE for diet planning: {tdee} kcal/day")
            user_profile_details_string = "Current user profile:\n- " + "\n- ".join(details)
        
        # Format chat history
        chat_history_string = "No previous conversation turns in this session yet."
        # We take MAX_HISTORY_TURNS * 2 because each turn has a user and an assistant message.
        # We also don't include the current user_input_prompt in the history yet.
        relevant_messages = st.session_state.messages[-(MAX_HISTORY_TURNS * 2):-1] # Get up to last N turns, excluding current user input
        
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
            user_question=user_input_prompt
        )
        
        try:
            if 'model' in globals(): # Check if LLM model is initialized
                # st.info(f"Sending to LLM:\n\n{final_llm_prompt}") # For debugging the prompt
                response = model.generate_content(final_llm_prompt)
                assistant_response = response.text
            else:
                assistant_response = "Sorry, the connection to the AI model is not available at the moment."
        except Exception as e:
            st.error(f"Error generating response from LLM: {e}")
            assistant_response = f"Sorry, I encountered an error while trying to respond. Please try again. Error: {e}"

        st.markdown(assistant_response)
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})

# # --- Main execution block (placeholder, as Streamlit handles the flow) ---
# if name == "main":
#  pass