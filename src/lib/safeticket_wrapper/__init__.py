#!/usr/bin/env python3
# ex: set tabstop=8 softtabstop=0 expandtab shiftwidth=2 smarttab:
import pickle
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from time import time
from typing import Dict, Any, List
from urllib.parse import urljoin

import requests
import atexit


class Event:
    created_email: str
    created_name: str
    event_ts: int
    id: int
    name: str
    settle_date: str
    settled: int
    tickets_on_offer: int
    tickets_remaining: int
    tickets_sold: str
    turnover_today: str
    turnover_total: str
    user_permissions: Dict[str, Any]

    def __init__(self, _json: Dict[str, Any]):
        self.created_email = _json.pop("created_email")
        self.created_name = _json.pop("created_name")
        self.event_ts = _json.pop("eventts")
        self.id = _json.pop("id")
        self.name = _json.pop("name")
        self.settle_date = _json.pop("settledate")
        self.settled = _json.pop("settled")
        self.tickets_on_offer = _json.pop("tickets_on_offer")
        self.tickets_remaining = _json.pop("tickets_remaining")
        self.tickets_sold = _json.pop("tickets_sold")
        self.turnover_today = _json.pop("turnover_today")
        self.turnover_total = _json.pop("turnover_total")
        self.user_permissions = _json.pop("user_permissions")


class Events:
    events: List[Event]
    has_unsettled_events_without_valid_bank_account: int
    settled_events: int
    sold: int
    today: str
    total: str

    def __init__(self, _json: Dict[str, Any]):
        self.events = [Event(event) for event in _json.pop("events")]
        self.has_unsettled_events_without_valid_bank_account = _json.pop(
            "has_unsettled_events_without_valid_bankaccount")
        self.settled_events = _json.pop("settled_events")
        self.sold = _json.pop("sold")
        self.today = _json.pop("today")
        self.total = _json.pop("total")


class EventsResult:
    data: Events
    status: str

    def __init__(self, _json: Dict[str, Any]):
        self.data = Events(_json.pop("data"))
        self.status = _json.pop("status")


class Ticket:
    name: str
    id: int

    def __init__(self, _json: Dict[str, Any]):
        self.name = _json.pop("name")
        self.id = _json.pop("id")


class Tickets:
    name: str
    tickets: List[Ticket]

    def __init__(self, _json: Dict[str, Any]):
        self.name = _json.pop("name")
        self.tickets = [Ticket(ticket) for ticket in _json.pop("tickets")]


class TicketsResult:
    data: Tickets
    status: str

    def __init__(self, _json: Dict[str, Any]):
        self.data = Tickets(_json.pop("data"))
        self.status = _json.pop("status")


class LoginError(BaseException):
    def __init__(self):
        super().__init__("status_code is '403', "
                         "this normally happens because you aren't logged in.")
        self.errors = 403


class Client(requests.Session):
    def __init__(self, organization: str, *args, **kwargs):
        # noinspection PyArgumentList
        super(Client, self).__init__(*args, **kwargs)

        self.prefix_url = f"https://{organization}.safeticket.dk"

    def request(self, method, url, *args, **kwargs):
        url = urljoin(self.prefix_url, url)

        start_time = time()
        resp = super(Client, self).request(
            method, url, *args, timeout=5, **kwargs
        )
        print("[DEBUG] Response time: {:.2f} secs".format(time() - start_time))

        return resp


class SafeTicket:
    _username = None
    _password = None
    _session = None

    def __init__(self, organization: str, username: str, password: str):
        self._username = username
        self._password = password
        self._session = Client(organization)
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
                url='/admin/login',
                data={
                    'conturl': '/admin/',
                    'email': self._username,
                    'password': self._password
                },
                allow_redirects=False,
            )

        # The page always return 200, but if there is a redirect (302) in the history
        # the login was a success, if not it failed
        if req.status_code == 302:
            cookie_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with open(cookie_path, "wb") as f:
                pickle.dump(self._session.cookies, f)

            return True
        else:
            return False

    def get_events(self, past: bool = False) -> EventsResult:
        req = self._session.get(
            url='/admin/api/event',
            params={
                'operation': 'list',
                'view': 'financial',
                'past': int(past),
            },
            headers={'X-Requested-With': 'XMLHttpRequest'})

        if req.status_code == 403:
            raise LoginError()

        return EventsResult(req.json())

    def get_event_tickets(self, event_id: int) -> TicketsResult:
        req = self._session.get(
            url='/admin/api/financial',
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
        return TicketsResult(req.json())

    def export_tickets_stats(self, event_id: int, ticket_ids: list) -> str:
        _data = {
            'submitted': 1,
            'id': event_id,
            'csv': 'Start+eksport+(CSV)'
        }

        for ticket_id in ticket_ids:
            _data['ticket{}'.format(ticket_id)] = 1

        req = self._session.post(
            url='/admin/eventexportcsv',
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
        self.assertEqual(r.status, 'OK')
        self.assertTrue(r.data)

    def test_30_get_event_tickets(self):
        self._safeticket.login()

        r = self._safeticket.get_events()
        event_ids = [e.id for e in r.data.events]

        e = self._safeticket.get_event_tickets(event_ids[0])
        self.assertEqual(e.status, 'OK')
        self.assertTrue(e.data)

    def test_31_get_event_tickets__no_login(self):
        self.assertRaises(LoginError, self._safeticket.get_event_tickets, 403)

    def test_32_get_event_tickets__invalid_event(self):
        self._safeticket.login()
        self.assertRaises(IndexError, self._safeticket.get_event_tickets, 404)

    def test_40_export_tickets_stats(self):
        self._safeticket.login()

        r = self._safeticket.get_events()
        event_ids = [e.id for e in r.data.events]

        e = self._safeticket.get_event_tickets(event_ids[0])

        ticket_ids = [t.id for t in e.data.tickets]
        self.assertTrue('";"' in self._safeticket.export_tickets_stats(event_ids[0], ticket_ids))

    def test_41_export_tickets_stats__no_login(self):
        self.assertRaises(LoginError, self._safeticket.get_event_tickets, 403)

    def test_42_export_tickets_stats__invalid_event(self):
        self._safeticket.login()
        self.assertRaises(IndexError, self._safeticket.get_event_tickets, 404)
