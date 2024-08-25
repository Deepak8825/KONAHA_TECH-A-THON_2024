from flask import Flask, render_template, request, jsonify, send_from_directory
import random
import json
import os
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import google.generativeai as genai
 

api_key = os.environ.get("API_KEY", "AIzaSyATsUQ7tEpykZkeeikK6o_86qlMLSo_um0")
genai.configure(api_key=api_key)
 

sia = SentimentIntensityAnalyzer()
 
app = Flask(__name__)
 

base_dir = os.path.dirname(os.path.abspath(__file__))
 

with open(os.path.join(base_dir, 'exercises.json'), 'r') as f:
    exercises = json.load(f)
 
with open(os.path.join(base_dir, 'quotes.json'), 'r') as f:
    quotes = json.load(f)
 
with open(os.path.join(base_dir, 'mental_health.json'), 'r') as f:
    mental_health_resources = json.load(f)
 
with open(os.path.join(base_dir, 'resources.json'), 'r') as f:
    resources = json.load(f)
 

questions = [
    ("How’s your day going?", ["Good", "Okay", "Not great"]),
    ("What’s your routine like?", ["Busy", "Balanced", "Relaxed"]),
    ("How are you feeling these days?", ["Happy", "Mixed", "Sad"]),
    ("Anything on your mind lately?", ["Yes", "A little", "No"]),
    ("Are you sleeping well?", ["Yes", "Sometimes", "No"]),
    ("Do you get time to relax?", ["Yes", "Sometimes", "No"])
]
 

user_responses = []
current_question_index = 0
conversation_stage = 'question'  
 
def get_stress_level():
    stress_score = 0
    for response in user_responses:
        sentiment = sia.polarity_scores(response)
        stress_score += sentiment['neg']
 
    if stress_score < 2:
        return "low"
    elif 2 <= stress_score < 3:
        return "medium"
    else:
        return "high"
 
 
 
@app.route('/')
def index():
    return render_template('index.html')
 
@app.route('/static/<path:filename>')
def custom_static(filename):
    return send_from_directory('static', filename)
 
def generate_response(user_input):
    
    if user_input.lower() in ['restart', 'yes', 'start over']:
        return "restart"
   
    if user_input.lower() == 'quit':
        return "quit"
 
    try:
        
        response = genai.generate_text(prompt=user_input)
        print(f"API Response: {response}")  
 
        
        if response.candidates and len(response.candidates) > 0:
            generated_text = response.candidates[0].get('output', 'No output found')
        else:
            generated_text = 'Sorry, no valid response generated.'
    except Exception as e:
        print(f"Exception occurred: {e}") 
        generated_text = "Sorry, I couldn't process your request: {}".format(str(e))
 
    return generated_text
 
@app.route('/chat', methods=['POST'])
def chat():
    global current_question_index, user_responses, conversation_stage
    user_input = request.json.get('message', '')
 
    if not user_input.strip():
        return jsonify({"message": "Please provide a valid response."})
 
    if conversation_stage == 'question':
        user_responses.append(user_input)
 
        if current_question_index == 0:
            response = {
                "message": "Hi there! I'm here to chat with you and help you manage stress. I’ll ask you a few questions to get started. Ready?",
                "question": questions[current_question_index][0],
                "answers": questions[current_question_index][1]
            }
            current_question_index += 1
        elif current_question_index >= len(questions):
            final_stress_level = get_stress_level()
            motivational_quote = random.choice(quotes).get('quote', 'Keep pushing forward!')
            stress_relaxation_exercise = random.choice(exercises).get('description', 'Try deep breathing exercises to relax.')
            wellness_tip = random.choice(mental_health_resources.get('wellness_tips', [{"tip": "Take time for yourself each day."}])).get('tip', 'Take time for yourself each day.')
 
            motivational_message = "Motivational Quote: " + motivational_quote
            exercise_message = "Stress Relaxation Exercise: " + stress_relaxation_exercise
            wellness_message = "Wellness Tip: " + wellness_tip
 
            resource_links = resources.get(final_stress_level, [])
            resources_message = "Mental Health Resources:\n" + "\n".join([f"{resource['name']}: {resource['link']}" for resource in resource_links])
 
            response = {
                "message": "Based on your responses, your stress level seems to be " + final_stress_level + ". Here are some resources that might help you:",
                "motivational_quote": motivational_message,
                "stress_relaxation_exercise": exercise_message,
                "wellness_tip": wellness_message,
                "resources": resources_message,
                "request": "Would you like to restart the conversation or continue chatting?"
            }

            print(response)
 
            conversation_stage = 'restart'
            user_responses = []
            current_question_index = 0
        else:
            question, answers = questions[current_question_index]
            response = {
                "question": question,
                "answers": answers
            }
            current_question_index += 1
 
    elif conversation_stage == 'chat':
        conversational_response = generate_response(user_input)
       
        
        if conversational_response == "restart":
            conversation_stage = 'question'
            user_responses = []
            current_question_index = 0
            response = {
                "message": "Great! Let's start over. I'll ask you the first question.",
                "question": questions[current_question_index][0],
                "answers": questions[current_question_index][1]
            }
            current_question_index += 1
        elif conversational_response == "quit":
            response = {
                "message": "Thank you for chatting with me! I hope you feel better. Have a great day!"
            }
            conversation_stage = 'quit'
            user_responses = []
            current_question_index = 0
        else:
            response = {
                "message": conversational_response
            }
 
    elif conversation_stage == 'restart':
        if user_input.lower() in ['restart', 'yes', 'start over']:
            conversation_stage = 'question'
            user_responses = []
            current_question_index = 0
            response = {
                "message": "Great! Let's start over. I'll ask you the first question.",
                "question": questions[current_question_index][0],
                "answers": questions[current_question_index][1]
            }
            current_question_index += 1
        elif user_input.lower() == 'quit':
            response = {
                "message": "Thank you for chatting with me! I hope you feel better. Have a great day!"
            }
            conversation_stage = 'quit'
            user_responses = []
            current_question_index = 0
        else:
            conversation_stage = 'chat'
            conversational_response = generate_response(user_input)
            response = {
                "message": conversational_response
            }
 
    return jsonify(response)
 
 
if __name__ == '__main__':
    app.run(debug=True)
 