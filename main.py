
from flask_script import Manager
from flask_migrate import MigrateCommand
from info import creat_app

# 创建web应用
from info.utils.response_code import RET, error_map

app = creat_app("dev")
# 创建管理器
mgr = Manager(app)

# 使用管理器生成迁移命令
mgr.add_command("news",MigrateCommand)

# 创建管理员账号
@mgr.option("-u",dest="username") # 将有参的函数生成为命令
@mgr.option("-p",dest="password") # 一次只能设置一个参数　使用：python main.py create_superuser -u xxx -p xxxx
def create_superuser(username,password):
    if not all([username,password]):
        app.logger.error("生成管理员失败")
        return

    from info.utils.models import User
    #　生成管理员　user 表的用户数据 is_admin字段设置为true
    user = User()
    user.mobile = username
    user.password = password
    user.nick_name = username
    user.is_admin = True

    from info import db
    db.session.add(user)
    try:
        db.session.commit()
    except Exception as e:
        app.logger.error("生成管理员失败: %s"% e)
        db.session.rollback()
        return
    app.logger.info("生成管理员成功")

# @mgr.command  # 这个装饰器可以将无参的函数生成为命令 python main.py demo 即可执行
# def demo():
#     print("demo")

if __name__ == '__main__':
    mgr.run()