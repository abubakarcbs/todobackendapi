# main.py
from contextlib import asynccontextmanager
from typing import Union, Optional, Annotated
from fastapi_helloworld import settings
from sqlmodel import Field, Session, SQLModel, create_engine, select
from fastapi import FastAPI, Depends, HTTPException


connection_string = str(settings.DATABASE_URL).replace(
    "postgresql", "postgresql+psycopg"
)


engine = create_engine(
    connection_string, connect_args={"sslmode": "require"}, pool_recycle=300
)

def get_db():
    db=Session(bind=engine)
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session,Depends(get_db)]




class Todo(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    content: str = Field(index=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating tables..")
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan, title="Hello World API with DB", 
    version="0.0.1",
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development Server"
        }
        ])


def get_session():
    with Session(engine) as session:
        yield session


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/todos/")
def create_todo(todo: Todo, session:db_dependency):
       
            session.add(todo)
            session.commit()
            session.refresh(todo)
            return todo
from fastapi import HTTPException

from fastapi import HTTPException, status

@app.put("/todos/{todo_id}")
def update_todos(todo_id: int, todo_update: Todo, session: Session = Depends(get_session)):
    existing_todo = session.query(Todo).filter(Todo.id == todo_id).first()
    if not existing_todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    for key, value in todo_update.dict().items():
        setattr(existing_todo, key, value)

    try:
        session.commit()
        return existing_todo
    except Exception as e:
        session.rollback()  
        raise HTTPException(status_code=500, detail=str(e))





@app.get("/todos/")
def read_todos(session:db_dependency):
       
            todos = session.exec(select(Todo)).all()
            return todos

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int, session: db_dependency):
    todo = session.get(Todo, todo_id)  
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    session.delete(todo) 
    session.commit()

    return {"message": "Todo deleted successfully"}  
