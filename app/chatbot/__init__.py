from flask import Blueprint

chatbot = Blueprint('chatbot', __name__, url_prefix='/chatbot')

from . import routes
