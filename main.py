from fastapi import Depends, FastAPI, HTTPException 
from pydantic import BaseModel, EmailStr
from typing import List 
from sqlalchemy import create_engine, Column, Integer, String, DateTime 
from sqlalchemy.ext.declarative import declarative_base 
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from datetime import datetime, timezone


# start mysql server
# create new sql db: book_manager_db
DATABASE_URL = "mysql://root:miles@localhost/book_manager_db"

# housekeeping
engine = create_engine(DATABASE_URL, connect_args={"charset": "utf8mb4"})  # Create the SQLAlchemy engine with charset.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # Session factory for managing DB sessions.

# declase db model
Base = declarative_base() 

# define db model
class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)  
    username = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False) 
    author = Column(String(500), nullable=False)
    date = Column(DateTime, default=datetime.now(timezone.utc))

# create app instance
app = FastAPI()

# create db session
def get_db():
    db = SessionLocal() 
    try:
        yield db  
    finally:
        db.close()

# pydantic validation
class BookCreate(BaseModel):
    username: str
    title: str 
    author: str 

class BookOut(BookCreate):
    id: int

    class Config:
        from_attributes = True

# create db tables
Base.metadata.create_all(bind=engine)

# CRUD Ops
# get all books in db
@app.get("/books", response_model=List[BookOut])
def get_books(db: Session = Depends(get_db)):
    books = db.query(Book).all() 
    return books  

# get book by specific id
@app.get("/books/{book_id}", response_model=BookOut)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()  
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book 

# create a new book and validate all parameters
@app.post("/books", response_model=BookOut)
def create_book(book: BookCreate, db: Session = Depends(get_db)):
    db_book = Book(
        username=book.username,
        title =book.title, 
        author=book.author,
    )
    db.add(db_book)  
    db.commit()  
    db.refresh(db_book)  
    return db_book 

# update book information
@app.put("/books/{book_id}", response_model=BookOut)
def update_book(book_id: int, updated_book: BookCreate, db: Session = Depends(get_db)):
    db_book = db.query(Book).filter(Book.id == book_id).first()  
    if not db_book: 
        raise HTTPException(status_code=404, detail="Book not found")
    
    db_book.username = updated_book.username 
    db_book.title = updated_book.title  
    db_book.author = updated_book.author  
    
    db.commit()  
    db.refresh(db_book)  
    return db_book 

# delete a book with specific id
@app.delete("/books/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db)):
    db_book = db.query(Book).filter(Book.id == book_id).first()  
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    db.delete(db_book) 
    db.commit()  
    return {"message": f"Book with ID {book_id} deleted"} 
