from datetime import timedelta

from flask import Flask,session
from flask_sqlalchemy import SQLAlchemy
from redis import Redis
from flask_session import Session
from flask_script import Manager
from flask_migrate import Migrate,MigrateCommand

app = Flask(__name__)


# 将配置信息封装到config类中
class Config:
    DEBUG = True    # 开启调试模式
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:3306/news"  # 设置数据库地址
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 不追踪数据库的变化
    REDIS_HOST = "127.0.0.1" # redis的ip
    REDIS_PORT = 6379   # redis的端口
    SESSION_TYPE = "redis"  # 设置session的存储方式
    SESSION_REDIS = Redis(host=REDIS_HOST,port=REDIS_PORT)
    SESSION_USE_SIGNER = True   # 设置session_id是否加密
    SECRET_KEY = "kNAgBQjBEQJ9Q/wmdO2gp2qfns+VMKX2sNo5ucxbELAkj1Ux10w+Qrupkp0Etw/j" # 设置应用秘钥,对session进行加密
    PERMANENT_SESSION_LIFETIME = timedelta(days=31) # 设置session过期时间


app.config.from_object(Config)

# 创建数据库链接
db = SQLAlchemy(app)
# 创建redis链接
redis = Redis(host=Config.REDIS_HOST,port=Config.REDIS_PORT)
# 初始化session存储器
Session(app)
# 创建管理器
mgr = Manager(app)
# 初始化迁移器
Migrate(app,db)
# 使用管理器生成迁移命令
mgr.add_command("news",MigrateCommand)

@app.route('/')
def index():

    return

if __name__ == '__main__':
    mgr.run()