# -*- coding: utf-8 -*-

from sqlalchemy import create_engine

from flask.ext.babel import lazy_gettext
from flask.globals import current_app
from werkzeug.local import LocalProxy

from .schema import db


import logging
logger = logging.getLogger(__name__)


def init_db(app):
    atlantis_connection_string = 'mysql+pymysql://{0}:{1}@{2}:3306'.format(
        app.config['DB_ATLANTIS_USER'],
        app.config['DB_ATLANTIS_PASSWORD'],
        app.config['DB_ATLANTIS_HOST']
    )

    # set netusers as default binding
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        "{}/netusers".format(atlantis_connection_string)
    )
    app.config['SQLALCHEMY_BINDS'] = {
        # 'netusers': "{}/netusers".format(atlantis_connection_string),
        'traffic': "{}/traffic".format(atlantis_connection_string),
    }

    db.init_app(app)

    for bind in [None, 'traffic']:
        engine = db.get_engine(app, bind=bind)
        conn = engine.connect()
        conn.execute("SET lock_wait_timeout=%s", (2,))
        conn.close()

    app.extensions['db_helios'] = create_engine(
        'mysql+pymysql://{0}:{1}@{2}:{3}/'.format(
            app.config['DB_HELIOS_USER'],
            app.config['DB_HELIOS_PASSWORD'],
            app.config['DB_HELIOS_HOST'],
            int(app.config['DB_HELIOS_PORT'])),
        echo=False, connect_args={'connect_timeout': app.config['SQL_TIMEOUT']}
    )


db_helios = LocalProxy(lambda: current_app.extensions['db_helios'])

DORMITORIES = [
    'Wundstraße 5',
    'Wundstraße 7',
    'Wundstraße 9',
    'Wundstraße 11',
    'Wundstraße 1',
    'Wundstraße 3',
    'Zellescher Weg 41',
    'Zellescher Weg 41A',
    'Zellescher Weg 41B',
    'Zellescher Weg 41C',
    'Zellescher Weg 41D',
    'Borsbergstraße 34',
]

STATUS = {
    1: (lazy_gettext('ok'), 'success'),
    2: (lazy_gettext('Nicht bezahlt, Netzanschluss gesperrt'), 'warning'),
    7: (lazy_gettext('Verstoß gegen Netzordnung, Netzanschluss gesperrt'),
        'danger'),
    9: (lazy_gettext('Exaktiv'), 'muted'),
    12: (lazy_gettext('Trafficlimit überschritten, Netzanschluss gesperrt'),
         'danger')
}


def sql_query(query, args=(), database=db_helios):
    """Prepare and execute a raw sql query.
    'args' is a tuple needed for string replacement.
    """
    conn = database.connect()
    result = conn.execute(query, args)
    conn.close()
    return result
