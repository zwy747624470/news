# 自定义过滤器实现格式转换
from flask import session, current_app, abort, g

from info.utils.models import User


def func_index_convert(value):

    # if value == 1:
    #     return "first"
    # elif value == 2:
    #     return "second"
    # elif value == 3:
    #     return "third"
    # else:
    #     return ""
    # 上面这种方式可以实现,下面用另一种方法
    index_dict = {1:"first",
                  2:"second",
                  3:"third"
                  }
    return index_dict.get(value,"")

def user_login_data():
    # 获取session中的user_id
    user_id = session.get("user_id")
    user = None
    if user_id: # 用户已登录
        # 根据user_id 取出用户数据
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)
            return abort(500)

    # user = user.to_dict() if user else None

    # 用返回值也行,用g容器也行
    # return user
    g.user = user