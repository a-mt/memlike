import settings
import web

# Make it work no matter the current directory
import sys

sys.path.insert(0, settings.ROOTDIR)
sys.setrecursionlimit(500)

from app import app
wsgiapp = app.wsgifunc()
