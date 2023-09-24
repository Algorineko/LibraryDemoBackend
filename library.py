from datetime import datetime, timedelta
from typing import Union
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
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
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
# 账号相关
class Token(BaseModel):
    access_token: str
    token_type: str
class TokenData(BaseModel):
    username: Union[str, None] = None
class Amount(BaseModel):
    username: str
    disabled: bool
class UserInDB(Amount):
    hashed_password: str
amounts = {
    "Zhang Jialiang": {
        "username": "Zhang Jialiang",
        "hashed_password": "$2b$12$HyRVrbq.gXSHaCdYJsQ2Kusu9rqSXvPZKeiPtmRKHWRjNBxJhU2y6",
        "disabled": False,
    }
}
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
def get_password_hash(password):
    return pwd_context.hash(password)
def get_user(amounts, username: str):
    if username in amounts:
        user_dict = dict(amounts[username])
        return UserInDB(**user_dict)
def authenticate_user(amounts, username: str, password: str):
    user = get_user(amounts, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user
def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(amounts, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user
async def get_current_active_user(current_user: Amount = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(amounts, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": form_data.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}
@app.get("/users/me/", response_model=Amount)
async def read_users_me(current_user: Amount = Depends(get_current_active_user)):
    return current_user
@app.get("/users/me/items/")
async def read_own_items(current_user: Amount = Depends(get_current_active_user)):
    return [{"item_id": "Foo", "owner": current_user.username}]
# 图书相关
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