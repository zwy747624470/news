from flask import Blueprint

# 创建蓝图对象
home_blu = Blueprint("home",__name__)

# 让视图函数和主程序建立关联
from info.modules.home import views