import praw
from flask import Flask, jsonify
import uuid
from datetime import datetime
from flask import request
import os 
from openai import OpenAI

from dotenv import load_dotenv
load_dotenv()

reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent='Mozilla/5.0' + str(uuid.uuid4()),
)

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)

def get_last_active_time(username):
    try:
        # Get the Redditor instance
        user = reddit.redditor(username)
        
        # Initialize the most recent activity to None
        most_recent_activity = None
        
        # Fetch recent comments and submissions and update the most recent activity
        for comment in user.comments.new(limit=1):
            most_recent_activity = comment.created_utc
        for submission in user.submissions.new(limit=1):
            if most_recent_activity is None or submission.created_utc > most_recent_activity:
                most_recent_activity = submission.created_utc
        
        # If no activity is found, the user has no comments or submissions
        if most_recent_activity is None:
            return None
        
        # Convert the timestamp to a human-readable format
        last_active_time = datetime.utcfromtimestamp(most_recent_activity).strftime('%Y-%m-%d %H:%M:%S UTC')
        
        return {'last_active_time': last_active_time}
    except Exception as e:
        message = f"An error occurred: {e}"
        print(message)
        return { "error": message }


app = Flask(__name__)

@app.route('/last_active_time', methods=['GET'])
def last_active_time():
    username = request.args.get('username')
    
    # Validate the username parameter
    if not username:
        return jsonify({"error": "Missing 'username' parameter"})
    
    result = get_last_active_time(username)
    return jsonify(result)

@app.route('/is_this_important', methods=['POST'])
def is_this_imoprtant():
    content = request.json['content']
    selection = request.json['selection']

    prompt = f"""Content:
{content}
Get an understanding of the content above and the main ideas it communicates. Assume that the reader wants to understand those ideas as quickly as possible while reading the article.

Now, consider the following excerpt from the content:
{selection}

On a scale of 1-5, rate the excerpt based on how worth reading the selection is in terms of whether or not it's pertinent to the reader. Respond according to the following JSON format: {{ rating: number, explanation: string }}
"""
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="gpt-4-turbo",
    )

    rating = chat_completion.choices[0].message.content
    
    return jsonify({"rating": rating})

@app.route('/summarize', methods=['POST'])
def summarize():
    content = request.json['content']

    prompt = f"""Content: {content}
Provide a bullet-point summary of the content above. 
"""
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="gpt-4-turbo",
    )

    summary = chat_completion.choices[0].message.content
    
    return jsonify({"summary": summary})
    

if __name__ == '__main__':
    app.run(debug=True)