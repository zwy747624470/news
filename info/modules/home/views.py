from info.modules.home import home_blu
from info import redis,db
import logging # python 内置的日志模块,日志既可以在控制台输出,也可以保存到文件中
# flask中默认的日志信息也是使用的logging模块,但是他没有往文件里保存

# 使用蓝图对象注册路由
@home_blu.route('/')
def index():

    return "index"
