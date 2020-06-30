from flask import render_template, g, abort

from info.modules.user import user_blu
from info.utils.common import user_login_data


# 显示个人中心
@user_blu.route("/user_info")
@user_login_data
def user_info():

    user = g.user
    if not user:
        return abort(403)

    return render_template("user.html")