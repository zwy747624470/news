from flask import render_template, current_app, session, jsonify, abort, request, g

from info.modules.home import home_blu
from info import redis,db
import logging # python 内置的日志模块,日志既可以在控制台输出,也可以保存到文件中
# flask中默认的日志信息也是使用的logging模块,但是他没有往文件里保存

# 使用蓝图对象注册路由
from info.utils.common import user_login_data
from info.utils.constants import HOME_PAGE_MAX_NEWS
from info.utils.models import User, News, Category
from info.utils.response_code import RET, error_map


@home_blu.route('/')
def index():
    user_login_data()
    user = g.user.to_dict() if g.user else None

    # 查询点击量排行前十的新闻
    try:
        rank_list = News.query.order_by(News.clicks.desc()).limit(10).all()
    except Exception as e:
        current_app.logger.error(e)
        rank_list = []

    # 查询所有的分类数据
    try:
        categories = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return abort(500)

    # 新闻网站需要SEO,主要采用后端渲染来完成模板替换
    return render_template("index.html",user=user,rank_list=rank_list,categories=categories)


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

@home_blu.route("/get_news_list")
def get_news_list():
    # 获取参数
    cid = request.args.get("cid")
    cur_page = request.args.get("cur_page")
    per_count = request.args.get("per_count",HOME_PAGE_MAX_NEWS)

    # 校验参数
    if not all([cid,cur_page]):
        return jsonify(errno=RET.PARAMERR,errmsg=error_map[RET.PARAMERR])

    # 字符串转数字
    try:
        cid = int(cid)
        cur_page = int(cur_page)
        per_count = int(per_count)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR,errmsg=error_map[RET.PARAMERR])

    # 数据库查询数据
    # 按照分类,当前页,每页展示数量查询数据
    try:

        if cid != 1:
            pn = News.query.filter(News.category_id==cid).order_by(News.create_time.desc()).paginate(cur_page,per_count)
        else:
            pn = News.query.order_by(News.create_time.desc()).paginate(cur_page,per_count)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    # 返回数据
    data = {
        "news_list": [news.to_dict() for news in pn.items],
        "total": pn.pages
    }

    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK],data=data)