# Import necessary libraries
import streamlit as st
from streamlit_option_menu import option_menu
from utils import TaskManager, authenticate_user

# Initialize task manager
task_manager = TaskManager()

# Authenticate user
if not authenticate_user(st.session_state):
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login") and username == "admin" and password == "admin":
        st.session_state['logged_in'] = True
else:
    st.stop()

# Streamlit app layout
st.title("D-Chipset App - To Do List")

if 'tasks' not in st.session_state:
    st.session_state['tasks'] = []

# Option menu for navigation
selected_page = option_menu(
    "Menu",
    ["Add Task", "Task List"],
    icons=['plus', 'list-task'],
    menu_icon="cast",
    default_index=0,
)

if selected_page == "Add Task":
    st.subheader("Add New Task")
    task_text = st.text_input("Task Text")
    if st.button("Add Task") and task_text:
        task_manager.add_task(task_text)
        st.success("Task added successfully!")

if selected_page == "Task List":
    st.subheader("Task List")
    tasks = task_manager.get_tasks()
    for task in tasks:
        completed = task['completed']
        task_text = task['text']
        if completed:
            st.markdown(f"- {task_text} <span style='text-decoration: line-through;'>[Completed]</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"- {task_text} [Not Completed]")

# Error handling and logging
try:
    if selected_page == "Add Task":
        # Add task error handling
        pass
    elif selected_page == "Task List":
        # Display task list error handling
        pass
except Exception as e:
    st.error(f"An error occurred: {e}")