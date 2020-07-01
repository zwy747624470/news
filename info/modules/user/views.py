from flask import render_template, g, abort, request, jsonify, current_app

from info import db
from info.modules.user import user_blu
from info.utils.common import user_login_data, upload_file
from info.utils.constants import QINIU_DOMIN_PREFIX, HOME_PAGE_MAX_NEWS, USER_COLLECTION_MAX_NEWS, \
    USER_FOLLOWED_MAX_COUNT
from info.utils.models import UserCollection, News, Category, User
from info.utils.response_code import RET, error_map


# 显示个人中心
@user_blu.route("/user_info")
@user_login_data
def user_info():

    user = g.user
    if not user:
        return abort(403)

    return render_template("user.html",user=user.to_dict())

# 显示基本资料
@user_blu.route("/base_info",methods=["GET","POST"])
@user_login_data
def base_info():
    # 判断用户是否登录
    user = g.user
    if not user:
        return abort(403)
    if request.method == "GET":
        return render_template("user_base_info.html", user=user.to_dict())

    # POST提交数据
    # 获取参数
    signature = request.json.get("signature")
    nick_name = request.json.get("nick_name")
    gender = request.json.get("gender")

    # 校验参数
    if not all([signature,nick_name,gender]):
        return jsonify(errno=RET.PARAMERR,errmsg=error_map[RET.PARAMERR])

    if gender not in ["MAN","WOMAN"]:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 数据库记录数据
    user.signature = signature
    user.nick_name = nick_name
    user.gender = gender

    db.session.add(user)
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    # 返回数据
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])

# 显示和修改头像
@user_blu.route("/pic_info",methods=["GET","POST"])
@user_login_data
def pic_info():
    # 判断用户是否登录
    user = g.user
    if not user:
        return abort(403)
    if request.method == "GET":
        return render_template("user_pic_info.html", user=user.to_dict())

    # POST提交数据
    # 获取参数
    avatar_file = request.files.get("avatar")
    # 读取上传文件的二进制数据
    try:
        img_bytes = avatar_file.read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR,errmsg=error_map[RET.PARAMERR])

    #  七牛云上传文件
    try:
        file_name = upload_file(img_bytes)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg=error_map[RET.THIRDERR])

    # 数据库记录数据
    user.avatar_url = file_name

    db.session.add(user)
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    # 返回数据 为了让前端可以修改头像，需要返回头像链接
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK],data=user.to_dict())

#　修改密码
@user_blu.route("/pass_info",methods=["POST"])
@user_login_data
def pass_info():

    # 判断用户是否登录
    user = g.user
    if not user:
        return abort(403)
    if request.method == "GET":
        return render_template("user_pic_info.html", user=user.to_dict())

    # 获取参数
    old_password = request.json.get("old_password")
    new_password = request.json.get("new_password")

    # 校验参数
    if not all([old_password,new_password]):
        return jsonify(errno=RET.PARAMERR,errmsg=error_map[RET.PARAMERR])
    if not user.check_passoword(old_password):
        return jsonify(errno=RET.PWDERR,errmsg=error_map[RET.PWDERR])

    # 数据库处理数据
    user.password = new_password
    db.session.add(user)
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg=error_map[RET.DBERR])

    # 返回结果
    return jsonify(errno=RET.OK,errmsg=error_map[RET.OK])

# 显示我的收藏
@user_blu.route("/collection")
@user_login_data
def collection():

    # 判断用户是否登录
    user = g.user
    if not user:
        return abort(403)

    # 获取参数
    p = request.args.get("p",1)

    # 校验参数
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        return abort(403)

    # 数据库行为
    try:
       pn = user.collection_news.order_by(UserCollection.create_time.desc()).paginate(p,USER_COLLECTION_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)
        return abort(500)

    # 返回数据
    data = {
        "news_list": [item.to_dict() for item in pn.items],
        "cur_page": pn.page,
        "total_page": pn.pages
    }

    return render_template("user_collection.html",data=data)

# 显示新闻发布页面和提交新闻数据
@user_blu.route("/news_release",methods=["GET","POST"])
@user_login_data
def news_release():
    # 判断用户是否登录
    user = g.user
    if not user:
        return abort(403)

    if request.method == "GET":

        try:
            categories = Category.query.filter(Category.id != 1).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
        return render_template("user_news_release.html", categories=categories)

    # POST提交数据
    # 获取参数
    title = request.form.get("title")
    category_id = request.form.get("category_id")
    digest = request.form.get("digest")
    index_image = request.files.get("index_image")
    content = request.form.get("content")

    # 校验参数
    if not all([title,category_id,digest,index_image,content]):
        return jsonify(errno=RET.PARAMERR,errmsg=error_map[RET.PARAMERR])

    try:
        category_id = int(category_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 数据库记录数据 : 生成一条新闻记录
    news = News()
    news.title = title
    news.category_id = category_id
    news.digest = digest
    news.content = content

    # 上传图片到七牛云
    try:
        img_bytes = index_image.read()
        file_name = upload_file(img_bytes)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg=error_map[RET.THIRDERR])

    news.index_image_url = QINIU_DOMIN_PREFIX + file_name

    # 设置其他字段
    news.source = "个人发布"
    news.user_id = user.id
    news.status = 1

    db.session.add(news)
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg=error_map[RET.DBERR])

    # 返回数据
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 显示新闻列表
@user_blu.route("/news_list")
@user_login_data
def news_list():

    # 判断用户是否登录
    user = g.user
    if not user:
        return abort(403)

    # 获取参数
    p = request.args.get("p",1)

    # 校验参数
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        return abort(403)

    # 数据库行为
    try:
       pn = user.news_list.order_by(News.create_time).paginate(p,USER_COLLECTION_MAX_NEWS)
       # pn = user.news_list.paginate(p,USER_COLLECTION_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)
        return abort(500)

    # 返回数据
    data = {
        "news_list": [item.to_review_dict() for item in pn.items],
        "cur_page": pn.page,
        "total_page": pn.pages
    }

    return render_template("user_news_list.html",data=data)

# 显示用户关注的所有作者
@user_blu.route("/user_follow")
@user_login_data
def user_follow():
    # 判断用户是否登录
    user = g.user
    if not user:
        return abort(403)

    # 获取参数
    p = request.args.get("p",1)

    # 校验参数
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        return abort(403)

    # 数据库行为
    try:
       pn = user.followed.paginate(p,USER_FOLLOWED_MAX_COUNT)
    except Exception as e:
        current_app.logger.error(e)
        return abort(500)

    # 返回数据
    data = {
        "author_list": [author.to_dict() for author in pn.items],
        "cur_page": pn.page,
        "total_page": pn.pages
    }

    return render_template("user_follow.html",data=data)
