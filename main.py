from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey
from sqlalchemy.future import select

# Database setup
DATABASE_URL = "sqlite+aiosqlite:///./social_media.db"

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to get DB session
async def get_db():
    async with SessionLocal() as session:
        yield session

# Models
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    is_admin = Column(Boolean, default=False)
    image_url = Column(String, nullable=True)

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, index=True)
    post_text = Column(Text)
    likes = Column(Integer, default=0)

# Pydantic Schemas
class UserCreate(BaseModel):
    username: str
    is_admin: bool = False
    image_url: Optional[str] = None

class UserResponse(UserCreate):
    id: int

class PostCreate(BaseModel):
    user_id: int
    title: str
    post_text: str

class PostResponse(PostCreate):
    id: int
    likes: int

# FastAPI App
app = FastAPI()

# Initialize database
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# User Endpoints
@app.post("/users/", response_model=UserResponse)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    new_user = User(**user.dict())
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@app.get("/users/", response_model=List[UserResponse])
async def get_users(name: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    query = select(User)
    if name:
        query = query.where(User.username == name)
    result = await db.execute(query)
    return result.scalars().all()

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.patch("/users/{user_id}/name")
async def update_user_name(user_id: int, name: str, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.username = name
    await db.commit()
    return {"message": "User name updated"}

@app.patch("/users/{user_id}/is_admin")
async def update_user_is_admin(user_id: int, is_admin: bool, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_admin = is_admin
    await db.commit()
    return {"message": "User admin status updated"}

@app.patch("/users/{user_id}/image_url")
async def update_user_image(user_id: int, image_url: str, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.image_url = image_url
    await db.commit()
    return {"message": "User image updated"}

@app.delete("/users/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    await db.commit()
    return {"message": "User deleted"}

# Post Endpoints
@app.post("/posts/", response_model=PostResponse)
async def create_post(post: PostCreate, db: AsyncSession = Depends(get_db)):
    new_post = Post(**post.dict())
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)
    return new_post

@app.get("/posts/", response_model=List[PostResponse])
async def get_posts(title: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    query = select(Post)
    if title:
        query = query.where(Post.title == title)
    result = await db.execute(query)
    return result.scalars().all()

@app.get("/posts/user/{user_id}", response_model=List[PostResponse])
async def get_posts_by_user(user_id: int, db: AsyncSession = Depends(get_db)):
    query = select(Post).where(Post.user_id == user_id)
    result = await db.execute(query)
    return result.scalars().all()

@app.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    post = await db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@app.patch("/posts/{post_id}/title")
async def update_post_title(post_id: int, title: str, db: AsyncSession = Depends(get_db)):
    post = await db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post.title = title
    await db.commit()
    return {"message": "Post title updated"}

@app.patch("/posts/{post_id}/post_text")
async def update_post_text(post_id: int, post_text: str, db: AsyncSession = Depends(get_db)):
    post = await db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post.post_text = post_text
    await db.commit()
    return {"message": "Post text updated"}

@app.patch("/posts/{post_id}/increment_likes")
async def increment_post_likes(post_id: int, db: AsyncSession = Depends(get_db)):
    post = await db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post.likes += 1
    await db.commit()
    return {"message": "Post likes incremented"}

@app.patch("/posts/{post_id}/decrement_likes")
async def decrement_post_likes(post_id: int, db: AsyncSession = Depends(get_db)):
    post = await db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post.likes -= 1
    await db.commit()
    return {"message": "Post likes decremented"}

@app.delete("/posts/{post_id}")
async def delete_post(post_id: int, db: AsyncSession = Depends(get_db)):
    post = await db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    await db.delete(post)
    await db.commit()
    return {"message": "Post deleted"}
