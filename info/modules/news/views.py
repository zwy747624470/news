from flask import current_app, jsonify, render_template, session, abort, g, request

from info import db
from info.modules.news import news_blu
from info.utils.common import user_login_data
from info.utils.models import News, User
from info.utils.response_code import RET, error_map


@news_blu.route("/<int:news_id>")
@user_login_data
def news_detail(news_id):
    #　从数据库查询对应的新闻数据
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg=error_map[RET.DBERR])
        # return abort(500)

    # user_login_data()
    user = g.user.to_dict() if g.user else None
    # 查询点击量排行前十的新闻
    try:
        rank_list = News.query.order_by(News.clicks.desc()).limit(10).all()
    except Exception as e:
        current_app.logger.error(e)
        rank_list = []
    # 将数据传入模版进行渲染
    return render_template("detail.html",news=news.to_dict(),user=user,rank_list=rank_list)

@news_blu.route("/news_collect",methods=["POST"])
@user_login_data
def news_collect():

    # 判断用户是否登录
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR,errmsg=error_map[RET.SESSIONERR])

    # 获取参数
    news_id = request.json.get("news_id")
    action = request.json.get("action")

    # 校验参数
    if not all([news_id,action]):
        return jsonify(errno=RET.PARAMERR,errmsg=error_map[RET.PARAMERR])
    try:
        news_id = int(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR,errmsg=error_map[RET.PARAMERR])
    if action not in ["collect","cancel_collect"]:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 数据库记录数据 : 添加和删除收藏数据
    # 获取新闻id
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg=error_map[RET.DBERR])
    if action == "collect" and news:    # 收藏
        user.collection_news.append(news)
    else: # 取消收藏
        user.collection_news.remove(news)
    db.session.add(user)
    db.session.commit()
    # json返回结果
    return jsonify(errno=RET.OK,errmsg=error_map[RET.OK])