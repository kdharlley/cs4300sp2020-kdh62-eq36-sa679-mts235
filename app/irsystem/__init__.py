from flask import Blueprint

# Define a Blueprint for this module (mchat)
irsystem = Blueprint('irsystem', __name__, url_prefix='/',
                     static_folder='static', template_folder='templates')

# Import all controllers
from .controllers.search_controller import *
from .controllers.search_controller_ml import *
from .controllers.search_controller_1 import *
from .controllers.search_controller_2 import *