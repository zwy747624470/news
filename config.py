# 将配置信息封装到config类中
from datetime import timedelta

from redis import Redis


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

# 不同的代码需要使用不同的配置信息 (配置子类化)
# 开发环境,项目开发阶段需要的代码环境
class DevelopmentConfig(Config):
    DEBUG = True

# 生产环境,项目上线后需要的代码环境(用户可以外网访问)
class ProductionConfig(Config):
    DEBUG = False

config_dict = {
    "dev":DevelopmentConfig,
    "pro":ProductionConfig
}