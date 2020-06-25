from info.modules.home import home_blu
from info import redis,db
# 使用蓝图对象注册路由
@home_blu.route('/')
def index():

    return "index"
