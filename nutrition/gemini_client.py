import os
import json
import requests
from django.conf import settings

class GeminiClient:
    """Client for interacting with Google's Gemini API"""

    def __init__(self, api_key=None, model_name=None):
        self.api_key = 'AIzaSyBVsVEtXS-4x6wn_hfE4lp4TyZqfR9LeBU'
        self.model_name = 'gemini-2.0-flash'

        if not self.api_key:
            raise ValueError("Gemini API key is required.")

    def generate_text(self, prompt):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        headers = { "Content-Type": "application/json" }
        data = {
            "contents": [
                {
                    "parts": [
                        { "text": prompt }
                    ]
                }
            ]
        }

        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code != 200:
            raise Exception(f"Error: {response.status_code}, {response.text}")

        result = response.json()
        try:
            return result['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError):
            raise Exception(f"Unexpected response format: {result}")

    def analyze_image(self, base64_image, prompt):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        headers = { "Content-Type": "application/json" }
        data = {
            "contents": [
                {
                    "parts": [
                        { "text": prompt },
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": base64_image
                            }
                        }
                    ]
                }
            ]
        }

        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code != 200:
            raise Exception(f"Error: {response.status_code}, {response.text}")

        result = response.json()
        try:
            return result['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError):
            raise Exception(f"Unexpected response format: {result}")
