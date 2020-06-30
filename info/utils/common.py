# 自定义过滤器实现格式转换
import functools

from flask import session, current_app, abort, g

from info.utils.models import User
from qiniu import Auth, put_file, etag, put_data


# 自定义过滤器 实现索引格式转换
def func_index_convert(value):

    # if value == 1:
    #     return "first"
    # elif value == 2:
    #     return "second"
    # elif value == 3:
    #     return "third"
    # else:
    #     return ""
    # 上面这种方式可以实现,下面用另一种方法
    index_dict = {1:"first",
                  2:"second",
                  3:"third"
                  }
    return index_dict.get(value,"")

# 获取用户登录信息
def user_login_data(func):

    @functools.wraps(func)  # 防止使用装饰器后,更改函数的标记
    def wrapper(*args,**kwargs):
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

        # user = user.to_dict() if user else None

        # 用返回值也行,用g容器也行
        # return user
        g.user = user
        return func(*args,**kwargs)
    return wrapper

# 封装七牛云 文件上传工具
def upload_file(data):
    access_key = "cK4-y8ULAb9neHvcPqIMksLnhKBBKHpWP6skfqc2"
    secret_key = "ZDJSXSF9hwCMfVIT39JcmrDZJMmOSUVb9OP9LcDV"
    q = Auth(access_key, secret_key)
    # 要上传的空间
    bucket_name = 'newsitem'
    # 上传后保存的文件名
    key = None
    # 生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, key, 3600)
    # 要上传文件的本地路径
    localfile = data
    ret, info = put_data(token, key, localfile)
    if ret is not None: # 上传成功
        file_name = ret.get("key")
        return file_name
    else: #　上传失败了
        raise Exception(info)