from flask import current_app, jsonify, render_template, session, abort, g, request

from info import db
from info.modules.news import news_blu
from info.utils.common import user_login_data
from info.utils.models import News, User, Comment
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

    user = g.user

    # 查询当前新闻是否被用户收藏
    is_collected = False
    if user: # 用户已登录
        if news in user.collection_news:
            is_collected = True


    # 查询当前新闻的所有评论
    try:
        comment_list = news.comments.order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg=error_map[RET.DBERR])

    # 查询哪些评论被当前用户点过赞
    comments = []
    for comment in comment_list:
        comment_dict = comment.to_dict()
        is_like = False
        if user:
            # 如果这个评论被用户点过赞,就设置is_like为True
            if comment in user.like_comments:
                is_like = True
        comment_dict["is_like"] = is_like
        comments.append(comment_dict)

    # 查询点击量排行前十的新闻
    try:
        rank_list = News.query.order_by(News.clicks.desc()).limit(10).all()
    except Exception as e:
        current_app.logger.error(e)
        rank_list = []

    user = user.to_dict() if user else None
    # 将数据传入模版进行渲染
    return render_template("detail.html",news=news.to_dict(),user=user,rank_list=rank_list,is_collected=is_collected,comment_list=comments)

# 新闻收藏
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
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg=error_map[RET.DBERR])

    # json返回结果
    return jsonify(errno=RET.OK,errmsg=error_map[RET.OK])

# 新闻的评论
@news_blu.route("/news_comment",methods=["POST"])
@user_login_data
def news_comment():
    # 判断用户是否登录
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR,errmsg=error_map[RET.SESSIONERR])

    # 获取参数
    news_id = request.json.get("news_id")
    comment_content = request.json.get("comment")
    parent_id = request.json.get("parent_id")

    # 校验参数
    if not all([news_id,comment_content]):
        return jsonify(errno=RET.PARAMERR,errmsg=error_map[RET.PARAMERR])

    try:
        news_id = int(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR,errmsg=error_map[RET.PARAMERR])

    # 数据库行为:添加一条评论数据
    comment = Comment()
    comment.content = comment_content
    comment.news_id = news_id
    comment.user_id = user.id
    if parent_id:
        try:
            parent_id = int(parent_id)
            comment.parent_id = parent_id
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR,errmsg=error_map[RET.PARAMERR])

    db.session.add(comment)
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg=error_map[RET.DBERR])
    # 返回数据:json
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK],data=comment.to_dict())


@news_blu.route("/comment_like",methods=["POST"])
@user_login_data
def comment_like():

    # 判断用户是否登录
    user = g.user
    if not user:    # 用户未登录
        return jsonify(errno=RET.SESSIONERR, errmsg=error_map[RET.SESSIONERR])
    # 获取参数
    comment_id = request.json.get("comment_id")
    action = request.json.get("action")

    # 校验参数
    if not all([comment_id,action]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    try:
        comment_id = int(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    if action not in ["add","remove"]:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 数据记录数据
    # 获取评论id对应的评论模型
    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    # 添加/删除点赞记录
    if action == "add": # 点赞
        user.like_comments.append(comment)
        # 点赞的数量加1
        comment.like_count += 1
    else:   # 取消点赞
        user.like_comments.remove(comment)
        # 点赞数量减1
        comment.like_count -= 1

    db.session.add(user)
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    # 返回数据
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])