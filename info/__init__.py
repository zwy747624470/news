import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template, g
from flask_migrate import Migrate
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from redis import Redis
from config import config_dict

# 将数据库链接对象定义为全局变量 以便于其他文件导入使用
db = None       # type:SQLAlchemy
redis = None    # type:Redis

# 设置日志
def setup_log(log_level):
    # 设置日志的记录等级
    logging.basicConfig(level=log_level)  # 调试debug级

    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)
    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(pathname)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


# 工厂函数: 由外界提供我们的物料,在函数内部封装我们对象的创建
def creat_app(Config):    # 封装web应用的创建过程
    Config = config_dict[Config]
    app = Flask(__name__)


    app.config.from_object(Config)
    global db,redis
    # 创建数据库链接
    db = SQLAlchemy(app)
    # 创建redis链接
    redis = Redis(host=Config.REDIS_HOST,port=Config.REDIS_PORT,decode_responses=True)
    # 初始化session存储器
    Session(app)

    # 初始化迁移器
    Migrate(app,db)

    # 注册蓝图对象
    from info.modules.home import home_blu
    app.register_blueprint(home_blu)
    from info.modules.passport import passport_blu
    app.register_blueprint(passport_blu)
    from info.modules.news import news_blu
    app.register_blueprint(news_blu)
    from info.modules.user import user_blu
    app.register_blueprint(user_blu)

    # 让模型文件和主程序建立关联
    from info.utils import models

    # 设置日志
    setup_log(Config.LOG_LEVEL)

    from info.utils.common import func_index_convert
    # 添加自定义过滤器
    app.add_template_filter(func_index_convert,"index_convert")

    from info.utils.common import user_login_data
    # 捕获404错误
    @app.errorhandler(404)
    @user_login_data
    def error_404(error):

        user = g.user.to_dict() if g.user else None

        # 渲染404页面

        return render_template("404.html",user=user)


    return app