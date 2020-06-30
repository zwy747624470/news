from flask import render_template, g, abort, request, jsonify, current_app

from info import db
from info.modules.user import user_blu
from info.utils.common import user_login_data, upload_file
from info.utils.constants import QINIU_DOMIN_PREFIX
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