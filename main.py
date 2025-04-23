from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from pydantic import BaseModel

from sqlalchemy import create_engine, inspect
from sqlalchemy import text

import os
from dotenv import load_dotenv
load_dotenv()

# DATABASE

DATABASE_URL= os.getenv("DATABASE_URL") 
engine = create_engine(DATABASE_URL,  client_encoding='utf8')

connection = engine.connect()
asd = inspect(engine)

result = connection.execute(
    text("""
        CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(255) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL);
         
        CREATE TABLE IF NOT EXISTS tasks (
        id SERIAL PRIMARY KEY,
        task VARCHAR(255) NOT NULL,
        deadline DATE NOT NULL,
        username VARCHAR(255) NOT NULL,
        FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE);

        CREATE TABLE IF NOT EXISTS macalisang ();
        """))

connection.commit()

print(result)
print(asd.get_table_names())

# API

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # This allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # This allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # This allows all headers
)

class User(BaseModel):
    username: str
    password: str 

class Task(BaseModel):
    task: str
    deadline: str 
    user: str
 
@app.post("/login/")
async def user_login(user: User):
    # Check if user exists
    result = connection.execute(
        text("""
            SELECT * FROM users
            WHERE username = :username AND password = :password;
            """).bindparams(username=user.username, password=user.password)
    )
    if not result.mappings().all():
        return {"status": "User Not Found!"}
    else:
        return {"status": "Logged in"}

@app.post("/create_user/")
async def create_user(user: User):
    # Check if user already exists
    result = connection.execute(
        text("""
            SELECT * FROM users
            WHERE username = :username;
            """).bindparams(username=user.username)
    )
    if result.mappings().all():
        raise HTTPException(status_code=400, headers={"X-Error": "User already exists!"}, detail="User already exists!")
    # Insert user into database
    try:
        connection.execute(
            text("""
                INSERT INTO users (username, password) VALUES (:username, :password);
                """).bindparams(username=user.username, password=user.password)
        )
        connection.commit()
        return {"status": "User Created!"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, headers={"X-Error": "Error Creating User!"}, detail="Error creating user!")

@app.post("/create_task/")
async def create_task(task: Task):
    # Check if user exists
    result = connection.execute(
        text("""
            SELECT * FROM users
            WHERE username = :username;
            """).bindparams(username=task.user)
    )
    if not result.mappings().all():
        return {"status": "User Not Found!"}
    # Insert task into database
    try:
        connection.execute(
            text("""
                INSERT INTO tasks (task, deadline, username) VALUES (:task, :deadline, :user);
                """).bindparams(task=task.task, deadline=task.deadline, user=task.user)
        )
        connection.commit()
        return {"status": "Task Created!"}
    except Exception as e:
        print(e)
        return {"status": "Error Creating Task!"}

@app.get("/get_tasks/")
async def get_tasks(name: str):
    # Check if user exists
    try:
        user_check = connection.execute(
            text("""
                SELECT * FROM users
                WHERE username = :username;
                """).bindparams(username=name)
        )
        if not user_check.mappings().all():
            return {"status": "User Not Found!"}
    except Exception as e:
        print(e)
        return {"status": "Error checking user!"}
    
    # Fetch tasks from database
    try:
        result = connection.execute(
            text("""
                SELECT task, deadline FROM tasks
                WHERE username = :username;
                """).bindparams(username=name)
        )
        tasks = result.mappings().all()
        # Format tasks as a list of strings
        formatted_tasks = [
            f"Task: {task['task']}, Deadline: {task['deadline']}" for task in tasks
        ]
        return {"tasks": formatted_tasks}
    except Exception as e:
        print(e)
        return {"status": "Error fetching tasks!"}