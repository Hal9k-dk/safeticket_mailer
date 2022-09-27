#!/usr/bin/env python3
# ex: set tabstop=8 softtabstop=0 expandtab shiftwidth=2 smarttab:
import pickle
import unittest
from datetime import datetime, timedelta
from pathlib import Path

import requests
import atexit


class LoginError(BaseException):
    def __init__(self):
        super().__init__("status_code is '403', "
                         "this normally happens because you aren't logged in.")
        self.errors = 403


class SafeTicket:
    _organization = None
    _username = None
    _password = None
    _session = None

    def __init__(self, organization: str, username: str, password: str):
        self._organization = organization
        self._username = username
        self._password = password
        self._session = requests.Session()
        atexit.register(self._cleanup)

    def _cleanup(self):
        self._session.close()

    def login(self) -> bool:
        """Return: True, if successful and False if failed"""
        cookie_path = Path("/tmp/.safeticket_mailer/cookie.jar")

        dt = datetime.now() - timedelta(minutes=10)
        if cookie_path.is_file() and cookie_path.stat().st_mtime > dt.timestamp():
            with open(cookie_path, "rb") as f:
                self._session.cookies.update(pickle.load(f))
            return True

        else:
            req = self._session.post(
                url='https://{}.safeticket.dk/admin/login'.format(self._organization),
                data={
                    'conturl': '/admin/',
                    'email': self._username,
                    'password': self._password
                })

        # The page always return 200, but if there is a redirect (302) in the history
        # the login was a success, if not it failed
        if req.status_code == 200 and req.history and req.history[0].status_code == 302:
            cookie_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with open(cookie_path, "wb") as f:
                pickle.dump(self._session.cookies, f)

            return True
        else:
            return False

    def get_events(self, past: bool = False) -> dict:
        req = self._session.get(
            url='https://{}.safeticket.dk/admin/api/event'.format(self._organization),
            params={
                'operation': 'list',
                'view': 'financial',
                'past': int(past),
            },
            headers={'X-Requested-With': 'XMLHttpRequest'})

        if req.status_code == 403:
            raise LoginError()

        return req.json()

    def get_event_tickets(self, event_id: int) -> dict:
        req = self._session.get(
            url='https://{}.safeticket.dk/admin/api/financial'.format(self._organization),
            data={
                'operation': 'eventexport',
                'id': event_id
            },
            headers={'X-Requested-With': 'XMLHttpRequest'})

        if req.status_code == 403:
            raise LoginError()

        if req.status_code == 500:
            raise IndexError("Error: status_code is '500', "
                             "this normally happens because of an invalid event_id")
        return req.json()

    def export_tickets_stats(self, event_id: int, ticket_ids: list) -> str:
        _data = {
            'submitted': 1,
            'id': event_id,
            'csv': 'Start+eksport+(CSV)'
        }

        for ticket_id in ticket_ids:
            _data['ticket{}'.format(ticket_id)] = 1

        req = self._session.post(
            url='https://{}.safeticket.dk/admin/eventexportcsv'.format(self._organization),
            data=_data)

        if req.status_code == 403:
            raise LoginError()

        if req.status_code == 500:
            raise IndexError("Error: status_code is '500', "
                             "this normally happens because of an invalid event_id")

        return req.text


class TestStringMethods(unittest.TestCase):
    def setUp(self):
        from config import Config
        self._safeticket = SafeTicket(
            Config().organization,
            Config().username,
            Config().password)

    def test_05_login__failed(self):
        from config import Config
        safeticket = SafeTicket(
            Config().organization,
            "tester_username",
            "Tester_password_1212")

        self.assertEqual(safeticket.login(), False)

    def test_10_login__success(self):
        self.assertEqual(self._safeticket.login(), True)

    def test_20_get_events(self):
        self._safeticket.login()

        r = self._safeticket.get_events()
        self.assertEqual(r['status'], 'OK')
        self.assertTrue('data' in r.keys())

    def test_30_get_event_tickets(self):
        self._safeticket.login()

        r = self._safeticket.get_events()
        event_ids = [e['id'] for e in r['data']['events']]

        e = self._safeticket.get_event_tickets(event_ids[0])
        self.assertEqual(e['status'], 'OK')
        self.assertTrue('data' in e.keys())

    def test_31_get_event_tickets__no_login(self):
        self.assertRaises(LoginError, self._safeticket.get_event_tickets, 403)

    def test_32_get_event_tickets__invalid_event(self):
        self._safeticket.login()
        self.assertRaises(IndexError, self._safeticket.get_event_tickets, 404)

    def test_40_export_tickets_stats(self):
        self._safeticket.login()

        r = self._safeticket.get_events()
        event_ids = [e['id'] for e in r['data']['events']]

        e = self._safeticket.get_event_tickets(event_ids[0])

        ticket_ids = [t['id'] for t in e['data']['tickets']]
        self.assertTrue('";"' in self._safeticket.export_tickets_stats(event_ids[0], ticket_ids))

    def test_41_export_tickets_stats__no_login(self):
        self.assertRaises(LoginError, self._safeticket.get_event_tickets, 403)

    def test_42_export_tickets_stats__invalid_event(self):
        self._safeticket.login()
        self.assertRaises(IndexError, self._safeticket.get_event_tickets, 404)
