from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()
# 设置允许跨域请求的来源
origins = [
    "http://localhost",
    "http://localhost:8080",  # Vue应用运行的地址
]
# 设置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)
class Book(BaseModel):
    id:int
    bookname:str
    author:str
    publisher:str

books = [
    Book(id=1, bookname="《红楼梦》", author="曹雪芹", publisher="人民文学出版社"),
    Book(id=2, bookname="《水浒传》", author="施耐庵", publisher="人民文学出版社"),
]
# 获取所有图书
@app.get("/books")
async def get_books():
    return {"books": books}
# 获取指定id图书
@app.get("/books/{book_id}")
async def get_book(book_id:int):
    for book in books:
        if book.id==book_id:
            return {"book":book}
    return {"message": f"未找到id为{book_id}的图书"}
# 添加图书
@app.post("/books")
async def create_books(book:Book):
    books.append(book)
    return {"message":"图书已添加"}
# 删除指定id图书
@app.delete("/books/{book_id}")
async def delete_book(book_id: int):
    global books
    try:
        book_to_delete = None
        for book in books:
            if book.id == book_id:
                book_to_delete = book
                break
        if book_to_delete:
            books.remove(book_to_delete)
            return {"message": f"id为{book_id}的图书已删除"}
        else:
            return {"message": f"未找到id为{book_id}的图书"}
    except Exception as e:
        logger.error(f"ID为{book_id}的图书出错: {str(e)}")
        return {"error": "删除图书时发生错误"}
# 更新指定id图书
@app.put("/books/{book_id}")
async def update_book(book_id:int,book_obj:Book):
    for book in books:
        if book.id==book_id:
            book.id=book_id
            book.bookname=book_obj.bookname
            book.author=book_obj.author
            book.publisher=book_obj.publisher
            return {"message":f"id为{book_id}的图书已更新"}
    return {"message": f"未找到id为{book_id}的图书"}
# 8.2--9.17