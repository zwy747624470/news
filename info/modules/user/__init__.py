from flask import Blueprint

user_blu = Blueprint("user",__name__)

from info.modules.user.views import *
