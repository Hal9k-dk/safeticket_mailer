#!/usr/bin/env python3
# ex: set tabstop=8 softtabstop=0 expandtab shiftwidth=2 smarttab:

import unittest
from io import StringIO
from csv import DictReader

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
  csv_content = safeticket.export_tickets_stats(event_ids[0], ticket_ids)

  _csv_reader = DictReader(
      StringIO(csv_content),
      skipinitialspace=True,
      delimiter=';',
      quotechar='"')

# pp([row for row in _csv_reader])
  ticket_types = {}
  ticket_unions = {}

  for row in _csv_reader:
    _count = ticket_types.get(row['Billettype'], 0)
    ticket_types[row['Billettype']] = _count + 1

    for member_tag in ['IDA Medlems ID', 'PROSA medlems ID', 'TL Medlems ID']:
      if row.get(member_tag, '') != '':
        _member_ids = ticket_unions.get(row['Billettype'], [])
        _member_ids.append(row[member_tag])
        ticket_unions[row['Billettype']] = _member_ids

  print('\n================(Ticket Stats)=================')
  pp(ticket_types)
  print('\n============(Ticket and Member IDs)============')
  pp(ticket_unions)


if __name__ == '__main__':
  main()


class TestStringMethods(unittest.TestCase):
  def setUp(self):
    pass

  def test_10_something(self):
    pass

