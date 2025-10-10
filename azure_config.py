# Azure Web App configuration for Python FastAPI
# This file configures the Azure Web App deployment

import os
from pathlib import Path

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent

# Azure Web App specific settings
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
ALLOWED_HOSTS = ['*']  # Azure Web App handles host validation

# Static files (if needed)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Azure Web App environment variables
WEBSITE_HOSTNAME = os.environ.get('WEBSITE_HOSTNAME')
WEBSITE_SITE_NAME = os.environ.get('WEBSITE_SITE_NAME')

# Database configuration from environment
DATABASE_URL = os.environ.get('DATABASE_URL', 
    'postgresql://retool:npg_yf3gdzwl4RqE@ep-silent-sun-afdlv6pj.c-2.us-west-2.retooldb.com/retool?sslmode=require')

# Logging configuration for Azure
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}