# -*- coding: utf-8 -*-
from flask import request, session, current_app
from flask.ext.login import current_user, AnonymousUserMixin
from ipaddress import IPv4Address

from werkzeug.local import LocalProxy
from sqlalchemy.exc import OperationalError

from . import sample, wu, hss, zeu

import operator


# TODO: Add temporarily disabled gerok module + dormitories
registered_datasources = [sample.datasource, wu.datasource]

registered_dormitories = sample.dormitories + wu.dormitories

premature_dormitories = hss.dormitories + zeu.dormitories


def init_datasources_dormitories(app):
    app.extensions['datasources'] = [
        source for source in registered_datasources
        if not source.debug_only or app.debug
    ]

    app.extensions['dormitories'] = [
        dorm for dorm in registered_dormitories
        if not dorm.datasource.debug_only or app.debug
    ]

    app.extensions['all_dormitories'] = (
        app.extensions['dormitories'] + premature_dormitories
    )


def list_all_dormitories():
    """Generate a list of all available dormitories (active & external).
    The list is alphabetically sorted by the second item of the tuple.
    """
    return sorted([
        (dormitory.name, dormitory.display_name)
        for dormitory in current_app.extensions['all_dormitories']
    ], key=operator.itemgetter(1))


def list_supported_dormitories():
    return sorted([
        (dormitory.name, dormitory.display_name)
        for dormitory in current_app.extensions['dormitories']
    ])


def init_context(app):
    for datasource in app.extensions['datasources']:
        datasource.init_context(app)


def dormitory_from_name(name):
    for dormitory in current_app.extensions['all_dormitories']:
        if dormitory.name == name:
            return dormitory
    return None


def preferred_dormitory_name():
    dormitory = dormitory_from_ip(request.remote_addr)
    return dormitory.name if dormitory else None


def current_datasource():
    if current_dormitory():
        return current_dormitory().datasource
    else:
        return None


def current_dormitory():
    return dormitory_from_name(session['dormitory'])


def datasource_from_ip(ip):
    dormitory = dormitory_from_ip(ip)
    if dormitory:
        return dormitory.datasource
    return None


def dormitory_from_ip(ip):
    for dormitory in current_app.extensions['dormitories']:
        if IPv4Address(str(ip)) in dormitory.subnets:
            return dormitory
    return None


def user_from_ip(ip):
    datasource = datasource_from_ip(ip)
    if datasource is not None:
        return datasource.user_class.from_ip(ip)
    else:
        return AnonymousUserMixin()


def current_user_supported():
    return LocalProxy(
        lambda: current_datasource().user_class.supported()
    )


def query_gauge_data():
    credit = {'data': None, 'error': False, 'foreign_user': False}
    try:
        if current_user.is_authenticated:
            user = current_user
        else:
            user = user_from_ip(request.remote_addr)
        credit['data'] = user.get_current_credit()
    except OperationalError:
        credit['error'] = True
    except AttributeError:
        credit['foreign_user'] = True
    return credit
