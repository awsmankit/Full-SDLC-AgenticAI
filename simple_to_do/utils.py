# Import necessary libraries
from Crypto.Cipher import AES
class TaskManager:
    def __init__(self):
        self.tasks = []

    def add_task(self, text):
        self.tasks.append({'text': text, 'completed': False})

    def get_tasks(self):
        return sorted(self.tasks, key=lambda x: x['text'])
class UserAuthenticator:
    @staticmethod
def authenticate_user(state):
        if 'logged_in' not in state:
            return False
        return state['logged_in']