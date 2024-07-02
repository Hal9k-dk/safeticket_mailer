#!/usr/bin/env python3
# ex: set tabstop=8 softtabstop=0 expandtab shiftwidth=2 smarttab:                              

import unittest
import requests
from hashlib import sha256


class SafeTicket:
    _version = 1
    _host = None
    _api_user = None
    _secret = None

    def __init__(self, host: str, api_user: str, secret: str):
        self._host = host
        self._api_user = api_user
        self._secret = secret

    def _calc_sha(self, data: list) -> str:
        return sha256('{version}:{user}:{args}:{secret}'.format(
            version=self._version,
            user=self._api_user,
            args=':'.join(data),
            secret=self._secret
        ).encode('utf-8')).hexdigest()

    def all_event(self, cash: int, t1: str, t2: str):
        data = {
            'version': self._version,
            'user': self._api_user,
            'cash': cash,
            't1': t1,
            't2': t2,
            'sha': self._calc_sha([cash, t1, t2])}

        return requests.post('https://{}/api/stats'.format(self._host), data)

    def single_event(self, _id, event: str, cash: int):
        data = {
            'version': self._version,
            'user': self._api_user,
            'event': event,
            'cash': cash,
            'sha': self._calc_sha([event, cash])}

        return requests.post('https://{}/api/stats/{}'.format(self._host, _id), data)


def single_order(self, _id: str):
    data = {
        'version': self._version,
        'user': self._api_user,
        'orderid': _id,
        'sha': self._calc_sha([_id])}

    return requests.post('https://{}/api/order'.format(self._host), data)


def all_order(self, events: list, t1: str, t2: str):
    _events = ','.join(events)
    sequence_number = ""
    data = {
        'version': self._version,
        'user': self._api_user,
        'events': _events,
        'sequence_number': sequence_number,
        't1': t1,
        't2': t2,
        'sha': self._calc_sha([_events, sequence_number, t1, t2])}

    return requests.post('https://{}/api/orders'.format(self._host), data)


def main():
    print('test')


if __name__ == '__main__':
    main()


class TestStringMethods(unittest.TestCase):
    def setUp(self):
        self.safeticket = SafeTicket(
            'webshop',
            '7ba7fbff4ef6933974c8c82b9419b6706338be8ab40d556980cbdfac5d868d20',
            ''
        )

    def test_calc_sha(self):
        self.assertEqual(
            self.safeticket._calc_sha(["0", "2011-10-01", "2011-11-01"]),
            '79a7f895e442b5c0e17323a4a3eab17a88c457c299342ea25381939f7a0d5a06'
        )
