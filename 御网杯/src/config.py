import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'this_is_a_very_secret_key_for_tax_system_2026')
    DATABASE = '/var/lib/sqlite/tax.db'
