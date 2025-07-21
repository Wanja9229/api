from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from contextlib import asynccontextmanager
import aiomysql

from database import Database
from models import Post, PostCreate, PostUpdate

# FastAPI 앱 생성
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시
    await Database.create_pool()
    yield
    # 종료 시
    await Database.close_pool()

app = FastAPI(lifespan=lifespan)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 헬스체크
@app.get("/")
async def root():
    return {"message": "Simple Posts API"}

# 모든 게시글 조회
@app.get("/posts", response_model=List[Post])
async def get_posts():
    async with Database.pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM simple_posts ORDER BY created_at DESC")
            posts = await cursor.fetchall()
            return posts

# 특정 게시글 조회
@app.get("/posts/{post_id}", response_model=Post)
async def get_post(post_id: int):
    async with Database.pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM simple_posts WHERE id = %s", (post_id,))
            post = await cursor.fetchone()
            if post is None:
                raise HTTPException(status_code=404, detail="Post not found")
            return post

# 게시글 생성
@app.post("/posts", response_model=Post)
async def create_post(post: PostCreate):
    async with Database.pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "INSERT INTO simple_posts (title, content) VALUES (%s, %s)",
                (post.title, post.content)
            )
            post_id = cursor.lastrowid
            
            # 생성된 게시글 반환
            await cursor.execute("SELECT * FROM simple_posts WHERE id = %s", (post_id,))
            new_post = await cursor.fetchone()
            return new_post

# 게시글 수정
@app.put("/posts/{post_id}", response_model=Post)
async def update_post(post_id: int, post: PostUpdate):
    async with Database.pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            # 게시글 존재 확인
            await cursor.execute("SELECT * FROM simple_posts WHERE id = %s", (post_id,))
            existing_post = await cursor.fetchone()
            if existing_post is None:
                raise HTTPException(status_code=404, detail="Post not found")
            
            # 업데이트할 필드만 처리
            update_data = post.dict(exclude_unset=True)
            if not update_data:
                return existing_post
            
            # UPDATE 쿼리 생성
            set_clause = ", ".join([f"{k} = %s" for k in update_data.keys()])
            values = list(update_data.values())
            values.append(post_id)
            
            await cursor.execute(
                f"UPDATE simple_posts SET {set_clause} WHERE id = %s",
                values
            )
            
            # 수정된 게시글 반환
            await cursor.execute("SELECT * FROM simple_posts WHERE id = %s", (post_id,))
            updated_post = await cursor.fetchone()
            return updated_post

# 게시글 삭제
@app.delete("/posts/{post_id}")
async def delete_post(post_id: int):
    async with Database.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            # 게시글 존재 확인
            await cursor.execute("SELECT id FROM simple_posts WHERE id = %s", (post_id,))
            if await cursor.fetchone() is None:
                raise HTTPException(status_code=404, detail="Post not found")
            
            # 삭제
            await cursor.execute("DELETE FROM simple_posts WHERE id = %s", (post_id,))
            return {"message": "Post deleted successfully"}