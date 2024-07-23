from dotenv import load_dotenv

import google.generativeai as genai
import os
import json

load_dotenv(override=True)
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')


def generate_questions(category: str, no_of_questions: int) -> str:
    question = model.generate_content(f"""
        I need you to generate {no_of_questions} creative, brain teasing and unique trivia question(s) for my trivia game app in the category {category}.
        Return the questions and their question id in a json array of objects.
        The 'question_id' should be the position of the question in the array starting from 1.
        The 'question' is the generated question.
        Do not add extra detail to the response as i have to parse the response and unexpected output would break my system
    """)
    return question.text


def evaluate_user_response(question: str, response: str) -> str:
    gemini_eval = model.generate_content(f"""
    A user Gave the answer {response} to the question {question}.
    Evaluate the users response and grade them out of 10.
    Your response should be as though you are talking to the user directly. This is a
    Return ur answer in json format ({"response": string, "grade": 3})
    """)
    print(gemini_eval.text)
    return json.loads(gemini_eval.text)

