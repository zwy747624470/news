from flask import current_app, jsonify, render_template, session, abort, g

from info.modules.news import news_blu
from info.utils.common import user_login_data
from info.utils.models import News, User
from info.utils.response_code import RET, error_map


@news_blu.route("/<int:news_id>")
def news_detail(news_id):
    #　从数据库查询对应的新闻数据
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg=error_map[RET.DBERR])
        # return abort(500)

    user_login_data()
    user = g.user.to_dict() if g.user else None
    # 查询点击量排行前十的新闻
    try:
        rank_list = News.query.order_by(News.clicks.desc()).limit(10).all()
    except Exception as e:
        current_app.logger.error(e)
        rank_list = []
    # 将数据传入模版进行渲染
    return render_template("detail.html",news=news.to_dict(),user=user,rank_list=rank_list)
