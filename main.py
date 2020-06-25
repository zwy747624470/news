from flask_script import Manager
from flask_migrate import MigrateCommand
from info import creat_app

# 创建web应用
app = creat_app("dev")
# 创建管理器
mgr = Manager(app)

# 使用管理器生成迁移命令
mgr.add_command("news",MigrateCommand)



if __name__ == '__main__':
    mgr.run()