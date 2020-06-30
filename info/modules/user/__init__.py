from flask import Blueprint

user_blu = Blueprint("user",__name__,url_prefix="/user")

from info.modules.user.views import *
