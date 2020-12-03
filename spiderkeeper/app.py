# -*- coding: utf-8 -*-
import sys
sys.path.append('/var/tmp/spider/')
from spiderkeeper.main import app
from spiderkeeper.main.views import main as main_blueprint


app.register_blueprint(main_blueprint)


app.run(host='0.0.0.0', port='9001')
