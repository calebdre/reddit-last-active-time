import praw
from flask import Flask, jsonify
import uuid
from datetime import datetime
from flask import request
from dotenv import load_dotenv
import os 

load_dotenv()

reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent='Mozilla/5.0' + str(uuid.uuid4()),
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

if __name__ == '__main__':
    app.run()