from flask import render_template, current_app, session, jsonify, abort

from info.modules.home import home_blu
from info import redis,db
import logging # python 内置的日志模块,日志既可以在控制台输出,也可以保存到文件中
# flask中默认的日志信息也是使用的logging模块,但是他没有往文件里保存

# 使用蓝图对象注册路由
from info.utils.models import User
from info.utils.response_code import RET, error_map


@home_blu.route('/')
def index():
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
    user = user.to_dict() if user else None

    # 新闻网站需要SEO,主要采用后端渲染来完成模板替换
    return render_template("index.html",user=user)


@home_blu.route("/favicon.ico")
def favico():
    """浏览器会自动向网站发起/favicon.ico请求来获取网站小图标"""
    # 网站只需实现该路由,并返回图标图片即可 只请求一次
    # with open的方法不会自动设置响应头,这里使用jsonfy方法不方便
    # with open("info/static/news/favicon.ico","rb") as f:
    #     content = f.read()

    # flask中提供了一个获取静态文件内容的方法send_static_file(会将内容包装为响应对象,并自动设置对应的content-type)
    response = current_app.send_static_file("news/favicon.ico")
    return response