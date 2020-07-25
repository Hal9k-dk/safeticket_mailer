#!/usr/bin/env python3
# ex: set tabstop=8 softtabstop=0 expandtab shiftwidth=2 smarttab:

import unittest

from lib.safeticket_wrapper import SafeTicket

from config import CONFIG

from pprint import pprint as pp

def main():
  safeticket = SafeTicket(
      CONFIG.organization,
      CONFIG.username,
      CONFIG.password)

  safeticket.login()

  events = safeticket.get_events()
  event_ids = [event['id'] for event in events['data']['events']
                if event['name'] == CONFIG.event_name]


  tickets = safeticket.get_event_tickets(event_ids[0])
  ticket_ids = [ticket['id'] for ticket in tickets['data']['tickets']]
  csv = safeticket.export_tickets_stats(event_ids[0], ticket_ids)

  print(csv)



if __name__ == '__main__':
  main()


class TestStringMethods(unittest.TestCase):
  def setUp(self):
    pass

  def test_10_something(self):
    pass

