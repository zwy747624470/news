import random
import re
from datetime import datetime

from flask import request, abort, current_app, make_response, Response, jsonify, session

from info import redis, db
from info.libs.captcha.pic_captcha import captcha
from info.libs.yuntongxun.sms import CCP
from info.modules.passport import passport_blu


from info.utils.constants import SMS_CODE_REDIS_EXPIRES, IMAGE_CODE_REDIS_EXPIRES
from info.utils.models import User
from info.utils.response_code import error_map, RET

# 获取图片验证码
@passport_blu.route("/get_img_code")
def get_img_code():

    # 获取图片key的参数
    image_code_id = request.args.get("image_code_id")

    # 校验参数
    if not image_code_id:
        return abort(403) # 403拒绝访问

    # 生成图片验证码
    img_name,img_text,img_bytes = captcha.generate_captcha()

    # 把图片的key和验证码文字保存到数据库 这里使用redis 1.根据图片key取值 2.可以设置过期时间 3.速度快
    try:
        redis.set("image_code_id_" + image_code_id, img_text,ex=IMAGE_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e) # 如果出错记录到错误日志中
        return abort(500)   # 返回服务器错误

    # 返回图片  自定义响应对象,修改响应类型
    response = make_response(img_bytes) # type: Response
    # 设置响应头content-type
    # response.headers["content-type"] = "image/jpeg"   # 这样稍微麻烦点,但效果是一样的
    response.content_type = "image/jpeg"

    return response


# 获取短信验证码
@passport_blu.route("/get_sms_code",methods=["POST"])
def get_sms_code():
    # 获取参数
    img_code_id = request.json.get("img_code_id")   # request.json 只要前端发送的是json格式的数据,它就会直接将其转换为字典格式
    mobile = request.json.get("mobile")
    img_code = request.json.get("img_code").lower()
    # 校验参数
    if not all([img_code_id,mobile,img_code]):
        return jsonify(errno=RET.PARAMERR,errmsg=error_map[RET.PARAMERR])   # 返回自定以的错误码
    # 校验手机号
    if not re.match(r"^1[0-9]\d{9}$",mobile):
        return jsonify(errno=RET.PARAMERR,errmsg=error_map[RET.PARAMERR])

    # 根据图片的key取出验证码文字
    try:
        real_img_text = redis.get("image_code_id_" + img_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg=error_map[RET.DBERR])
    # 校验验证码文字
    if real_img_text.lower() != img_code:
        # 验证码不正确
        return jsonify(errno=RET.PARAMERR,errmsg=error_map[RET.PARAMERR])

    # 发送短信之前判断用户是否存在
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg=error_map[RET.DBERR])

    if user:
        return jsonify(errno=RET.DATAEXIST,errmsg=error_map[RET.DATAEXIST])
    # 生成一个随机的短信验证码
    sms_num = "%04d" % random.randint(0,9999)
    # ***************************************************************************************
    # 项目开启后,需要把这里打开
    # # 发送短信
    # ccp = CCP()
    # # 注意： 测试的短信模板编号为1
    # result = ccp.send_template_sms(mobile, [sms_num, SMS_CODE_REDIS_EXPIRES], 1)
    # if result != 0:
    #     return jsonify(errno=RET.THIRDERR,errmsg=error_map[RET.THIRDERR])
    # ****************************************************************************************
    # 保存短信验证码
    try:
        redis.set(mobile,sms_num,ex=SMS_CODE_REDIS_EXPIRES*60)
    except Exception as e:
        current_app.logger.error(e)
        return abort(500)

    # 打印出验证码,省钱,项目开启需要注释掉
    current_app.logger.info("短信验证码",sms_num)

    # json形式返回结果
    return jsonify(errno=RET.OK,errmsg=error_map[RET.OK])

#　用户注册
@passport_blu.route("/register",methods=["POST"])
def register():
    # 获取参数
    sms_code = request.json.get("sms_code")
    mobile = request.json.get("mobile")
    password = request.json.get("password")

    # 校验参数
    if not all([sms_code,mobile,password]):
        return jsonify(errno=RET.PARAMERR,errmsg=error_map[RET.PARAMERR])
    # 校验手机号
    if not re.match(r"^1[0-9]\d{9}$",mobile):
        return jsonify(errno=RET.PARAMERR,errmsg=error_map[RET.PARAMERR])
    # 校验短信验证码
    try:
        real_sms_code = redis.get(mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg=error_map[RET.DBERR])

    if real_sms_code != sms_code:
        return jsonify(errno=RET.PARAMERR,errmsg=error_map[RET.PARAMERR])
    # 数据库记录手机号密码
    user = User()
    user.mobile = mobile
    # 使用计算型属性,封装加密过程
    user.password = password


    user.nick_name = mobile
    db.session.add(user)
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg=error_map[RET.DBERR])
    # 使用session记录用户的登录状态
    session["user_id"] = user.id

    # 跳转到首页
    return jsonify(errno=RET.OK,errmsg=error_map[RET.OK])


# 用户登录
@passport_blu.route("/login",methods=["POST"])
def login():
    # 获取参数
    mobile = request.json.get("mobile")
    password = request.json.get("password")
    # 校验参数
    if not all([mobile,password]):
        return jsonify(errno=RET.PARAMERR,errmsg=error_map[RET.PARAMERR])
    # 数据库查询用户数据
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR,errmsg=error_map[RET.PARAMERR])

    if not user:
        return jsonify(errno=RET.NODATA,errmsg=error_map[RET.NODATA])
    # 校验密码
    if not user.check_passoword(password):
        return jsonify(errno=RET.PWDERR,errmsg=error_map[RET.PWDERR])
    # 用户状态保持
    session["user_id"] = user.id
    # 用户最后登录时间
    user.last_login = datetime.now() # 记录用户的最后登录时间
    # 这样也可以实现提交, sqlalchemy提供了一个配置,可以在请求结束后自动提交,但是有bug,没有回滚,这里没有使用
    db.session.add(user)
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    # 返回结果
    return jsonify(errno=RET.OK,errmsg=error_map[RET.OK])