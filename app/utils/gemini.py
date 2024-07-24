from dotenv import load_dotenv

import google.generativeai as genai
import os

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


def evaluate_user(question: str, response: str) -> str:
    gemini_eval = model.generate_content(f"""
    A player in my trivia game gave the answer {response} to the question {question}.
    Evaluate the users response and grade them out of 10.
    Your response should be as though you are talking to the user directly.
    Make the response brief and direct as possible.
    Return the response and grade as a json object without the preceding ```json and following ```.
    Do not add extra detail/formating to the response as i have to parse the response and unexpected output would break my system.
    """)
    return gemini_eval.text