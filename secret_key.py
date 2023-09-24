# import secrets
# random_string = secrets.token_hex(32)
# print(random_string)
# print(len(random_string))
# 5e34abeb9c9c82509a05aa30a79912f59b0ee48448b3f2b246368c1760dd165a

from passlib.context import CryptContext
# 创建 CryptContext 对象
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# 要哈希的密码
password = "1145141919810"
# 生成哈希密码
hashed_password = pwd_context.hash(password)
# 打印哈希后的密码
print(hashed_password)