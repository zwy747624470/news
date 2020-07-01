from flask import request, render_template, current_app, redirect, url_for, session

from info.modules.admin import admin_blu

# 后台登录
from info.utils.models import User


@admin_blu.route("/login",methods=["GET","POST"])
def login():

    if request.method == "GET":
        is_admin = session.get("is_admin")
        if is_admin:
            return  redirect(url_for("admin.index"))
        return render_template("admin/login.html")

    # 获取参数
    username = request.form.get("username")
    password = request.form.get("password")

    # 校验参数
    if not all([username,password]):
        return render_template("admin/login.html",errmsg="参数不足")

    # 根据用户名查询用户
    try:
        user = User.query.filter(User.mobile==username,User.is_admin==True).first()
    except Exception as e:
        current_app.logger.error(e)
        return render_template("admin/login.html",errmsg="数据库查询失败")

    if not user:
        return render_template("admin/login.html", errmsg="该管理员不存在")

    # 验证账号密码
    if user.check_passoword(password) == False:
        return render_template("admin/login.html", errmsg="密码错误")

    # 记录用户登录状态
    session["user_id"] = user.id
    session["is_admin"] = True

    # 验证通过,跳到后台首页
    return redirect(url_for("admin.index"))

# 后台退出登录
@admin_blu.route("/logout")
def logout():
    # 删除session数据
    session.pop("user_id",None)
    session.pop("is_admin",None)
    return redirect(url_for("admin.login"))


# 后台首页
@admin_blu.route("/index")
def index():
    return render_template("admin/index.html")
