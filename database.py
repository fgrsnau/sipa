#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine


dormitories = [
    u'Wundstraße 5',
    u'Wundstraße 7',
    u'Wundstraße 9',
    u'Wundstraße 11',
    u'Wundstraße 1',
    u'Wundstraße 3',
    u'Zellescher Weg 41',
    u'Zellescher Weg 41A',
    u'Zellescher Weg 41B',
    u'Zellescher Weg 41C',
    u'Zellescher Weg 41D'
]

status = {
    1: u'Bezahlt, verbunden',
    2: u'Nicht bezahlt, Netzanschluss gesperrt',
    7: u'Verstoß gegen Netzordnung, Netzanschluss gesperrt',
    12: u'Trafficlimit überschritten, Netzanschluss gesperrt'
}


def sql_query(query, args=None):
    """Prepare and execute a raw sql query.
    'args' is a tuple needed for string replacement.
    """
    conn = db.connect()
    result = conn.execute(query, args)
    conn.close()
    return result


def query_userinfo(username):
    """Executes select query for the username and returns a prepared dict.

    * Dormitory IDs in Mysql are from 1-11, so we map to 0-10 with "x-1".

    Returns "-1" if a query result was empty (None), else
    returns the prepared dict.
    """
    user = sql_query(
        "SELECT nutzer_id, wheim_id, etage, zimmernr, status "
        "FROM nutzer "
        "WHERE unix_account = %s",
        (username,)
    ).fetchone()

    if not user:
        return -1

    computer = sql_query(
        "SELECT c_etheraddr, c_ip, c_hname, c_alias "
        "FROM computer "
        "WHERE nutzer_id = %s",
        (user['nutzer_id'])
    ).fetchone()

    if not computer:
        return -1

    user = {
        'id': user['nutzer_id'],
        'address': u"{0} / {1} {2}".format(
            dormitories[user['wheim_id']-1],
            user['etage'],
            user['zimmernr']
        ),
        'status': status[user['status']],
        'ip': computer['c_ip'],
        'mac': computer['c_etheraddr'].upper(),
        'hostname': computer['c_hname'],
        'hostalias': computer['c_alias']
    }

    return user


db = create_engine('mysql+mysqldb://buzz:word@127.0.0.1:3306/netusers', echo=False)