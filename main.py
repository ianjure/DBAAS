from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
        user VARCHAR(255) NOT NULL,
        FOREIGN KEY (user) REFERENCES users(username) ON DELETE CASCADE);

        CREATE TABLE IF NOT EXISTS macalisang ();
        """))

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
            """), username=user.username, password=user.password)
    if not result.mappings().all():
        return {"status": "User Not Found!"}
    else:
        return {"status": "Logged In!"}

@app.post("/create_user/")
async def create_user(user: User):
    # Check if user already exists
    result = connection.execute(
        text("""
            SELECT * FROM users
            WHERE username = :username;
            """), username=user.username)
    if result.mappings().all():
        return {"status": "User already exists!"}
    # Insert user into database
    try:
        connection.execute(
            text("""
                INSERT INTO users (username, password) VALUES (:username, :password);
                """), username=user.username, password=user.password)
        connection.commit()
        return {"status": "User Created!"}
    except Exception as e:
        print(e)
        return {"status": "Error Creating User!"}

@app.post("/create_task/")
async def create_task(task: Task):
    # Check if user exists
    result = connection.execute(
        text("""
            SELECT * FROM users
            WHERE username = :username;
            """), username=task.user)
    if not result.mappings().all():
        return {"status": "User Not Found!"}
    # Insert task into database
    try:
        connection.execute(
            text("""
                INSERT INTO tasks (task, deadline, user) VALUES (:task, :deadline, :user);
                """), task=task.task, deadline=task.deadline, user=task.user)
        connection.commit()
        return {"status": "Task Created!"}
    except Exception as e:
        print(e)
        return {"status": "Error Creating Task!"}

@app.get("/get_tasks/")
async def get_tasks(name: str):
    # Check if user exists
    try:
        connection.execute(
            text("""
                SELECT * FROM users
                WHERE username = :username;
                """), username=name)
    except Exception as e:
        print(e)
        return {"status": "User Not Found!"}
    # Fetch tasks from database
    result = connection.execute(
        text("""
            SELECT * FROM tasks
            WHERE user = :username;
            """), username=name)
    tasks = result.mappings().all()
    return {"tasks": tasks}
