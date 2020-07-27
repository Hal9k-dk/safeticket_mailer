#!/usr/bin/env python3
# ex: set tabstop=8 softtabstop=0 expandtab shiftwidth=2 smarttab:

import sys
import argparse
from io import StringIO
from csv import DictReader
from pprint import pprint as pp

import smtplib, ssl
from email.mime.text import MIMEText

#from pyexcel_ods3 import save_data
from tabulate import tabulate

from lib.safeticket_wrapper import SafeTicket
from config import CONFIG




def args_parser():
  parser = argparse.ArgumentParser(description='SafeTicket Mailer')
  parser.add_argument('--debug', dest='debug', action='store_true',
      default=False, help='Print a lot of info')

  parser.add_argument('--events', dest='events', action='store_true',
      default=False, help='Print all events')
  parser.add_argument('--tickets', dest='tickets', action='store_true',
      default=False, help='Print all the types of ticket of an event')
  parser.add_argument('--ticket-fields', dest='ticket_fields', action='store_true',
      default=False, help='Print all the possible fields existion for the tickets')
  parser.add_argument('--ticket-stats', dest='ticket_stats', action='store_true',
      default=False, help='Print ticket types and there stats for the event')
  parser.add_argument('--show-emails', dest='show_emails', action='store_true',
      default=False, help='Display the email there is going to be sendt')
  parser.add_argument('--send-emails', dest='send_emails', action='store_true',
      default=False, help='This will send the emails to the unions')

  # Print --help message if now arguments
  if len(sys.argv)==1:
    parser.print_help(sys.stderr)
    sys.exit(1)

  return parser.parse_args()

def main():
  args = args_parser()  

  safeticket = SafeTicket(
      CONFIG.organization,
      CONFIG.username,
      CONFIG.password)

  safeticket.login()

  # Look through all the events and find the one we need
  events = safeticket.get_events()
  event_ids = [event['id'] for event in events['data']['events']
                if event['name'] == CONFIG.event_name]

  if args.events or args.debug:
    pp(events['data']['events'])

  # Get all the data about ticket types from the selected `event`
  if len(event_ids) == 1:
    tickets = safeticket.get_event_tickets(event_ids[0])
  else:
    print('There was no event for the name "{}", try the --events args.'.format(CONFIG.event_name),
        file=sys.stderr)
    sys.exit(2)
  # Filter a the ticket types IDs into a list
  ticket_ids = [ticket['id'] for ticket in tickets['data']['tickets']]
  # Export ticket stats from the event into a CSV file
  csv_content = safeticket.export_tickets_stats(event_ids[0], ticket_ids)

  # Parse the CSV file
  _csv_reader = DictReader(
      StringIO(csv_content),
      skipinitialspace=True,
      delimiter=';',
      quotechar='"')

  # Contains all the ticket types and how many there have been sold of them
  ticket_types = {}

  # Doing counting of the tickets
  for row in _csv_reader:
    l = ticket_types.get(row['Billettype'], [])
    l.append(row)
    ticket_types[row['Billettype']] = l

  if args.tickets or args.debug:
    print('\n============(All The Tickets Types)============')
    pp(sorted([ticket['name'] for ticket in tickets['data']['tickets']]))
  if args.ticket_fields or args.debug:
    print('\n===(All The Possible Fields of The Tickets)====')
    pp(sorted(_csv_reader.fieldnames))
  if args.ticket_stats or args.debug:
    print('\n================(Ticket Stats)=================')
    pp([{k: len(v)} for k, v in ticket_types.items()])


  for union in CONFIG.unions:
    fields = CONFIG.ticket_fields + union['ticket_fields_extra']
    ticket_info_text = []
    for ticket_type_name in union['ticket_type_names']:
      data = []
      try:
        for ticket in ticket_types[ticket_type_name]:
          data.append([ticket[field] for field in fields])
      except KeyError as e:
        print("Error: The fields {} doesn't exist, check the variable 'ticket_fields' in the config.py file".format(e))
        sys.exit(1)

      ticket_info_text.append('{}:\n{}\nAntal billet soldt: {}'.format(
          ticket_type_name,
          tabulate(data, headers=fields),
          len(ticket_types[ticket_type_name]),
      ))

    msg = CONFIG.email_template.format(
       to_name=union['to_name'],
       from_name=union['from_name'],
       union_name=union['name'],
       ticket_info_text='\n\n'.join(ticket_info_text),
       extra_text=union['extra_text'])

    if args.show_emails or args.debug:
      print('\n============(Mail - {})============'.format(union['name']))
      print('TO:      {}'.format(union['to_email']))
      print('FROM:    {}'.format(union['from_email']))
      print('SUBJECT: {}'.format(union['subject']))
      print('\n---------------------------')
      print(msg)

    if args.send_emails:
      context = ssl.create_default_context()
      with smtplib.SMTP_SSL(CONFIG.SMTP.host, CONFIG.SMTP.port, context=context) as smtpObj:
        email = MIMEText(msg)
        email['To']      = union['to_email']
        email['From']    = union['from_email']
        email['Subject'] = union['subject']
        smtpObj.login(CONFIG.SMTP.username, CONFIG.SMTP.password)
        smtpObj.sendmail(union['from_email'], union['to_email'], email.as_string())
 

if __name__ == '__main__':
  main()



