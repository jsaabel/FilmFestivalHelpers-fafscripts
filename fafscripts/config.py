import os
import json

with open ('/etc/config.json') as config_file:
    config = json.load(config_file)

class Config:
  SECRET_KEY = config.get('SECRET_KEY')
  SQLALCHEMY_DATABASE_URI = config.get('SQLALCHEMY_DATABASE_URI')
  NOTION_API_KEY = config.get('NOTION_API_KEY')
  WP_API_KEY = config.get('WP_API_KEY')
  WP_BASE_URL = config.get('WP_BASE_URL')
  WP_USER = config.get('WP_USER')
  FESTIVAL_URL = config.get('FESTIVAL_URL')
  DROPBOX_REFRESH_TOKEN = config.get('DROPBOX_REFRESH_TOKEN')
  DROPBOX_APP_KEY = config.get('DROPBOX_APP_KEY')
  DROPBOX_APP_SECRET = config.get('DROPBOX_APP_SECRET')
  TEMPLATES_AUTO_RELOAD = True
