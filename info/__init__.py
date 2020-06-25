from flask import Flask
from flask_migrate import Migrate
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from redis import Redis
from config import config_dict

# 将数据库链接对象定义为全局变量 以便于其他文件导入使用
db = None       # type:SQLAlchemy
redis = None    # type:Redis

# 工厂函数: 由外界提供我们的物料,在函数内部封装我们对象的创建
def creat_app(Config):    # 封装web应用的创建过程
    Config = config_dict[Config]
    app = Flask(__name__)


    app.config.from_object(Config)
    global db,redis
    # 创建数据库链接
    db = SQLAlchemy(app)
    # 创建redis链接
    redis = Redis(host=Config.REDIS_HOST,port=Config.REDIS_PORT)
    # 初始化session存储器
    Session(app)

    # 初始化迁移器
    Migrate(app,db)

    # 注册蓝图对象
    from info.modules.home import home_blu
    app.register_blueprint(home_blu)

    # 让模型文件和主程序建立关联
    from info.utils import models

    return app