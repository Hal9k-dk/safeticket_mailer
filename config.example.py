# ex: set tabstop=8 softtabstop=0 expandtab shiftwidth=2 smarttab:

class CONFIG:
  # Login info for Safeticket.dk
  organization = 'example' # EXAMPLE.safeticket.dk
  username = 'someone' # Normally, this is an email address
  password = 'secret'

  # SMTP (mail) server config (currently, only SSL is supported)
  class SMTP:
    host = 'example.com'
    port = 587 # '25, 465, 587'
    username = 'someone'
    password = 'secret'

  # List events with the --events argument
  # Select the event
  event_name = 'the name of the event' # Example: "SummerHack 2020"

  # List fields from the ticket to include in the mail when listing ticket soldt.
  # The --ticket-fields argument will list all possible fields.
  ticket_fields = ['Navn', 'Email', 'Addresse', 'Addresse2']

  # Create a list of all the unions that needs and email and what it should contain
  unions = [{
    # Name of the Union
    'name': 'Union1',
    # Subject of The Email
    'subject': 'Ticket soldt so far',
    # The of the name of the reciever in the Email Template
    'to_name':  'Union Person',
    # The of the email-address of the reciever of the email
    'to_email': 'Some Persen <sp@union.org>',
    # The of the name of the sender in the Email Template
    'from_name':  'Event Persen',
    # Extra text added efter the name of the sender. E.g. a phone no.
    'extra_text': 'Phone Nr. 8888 8888 ',
    # The of the email-address of the sender of the email
    'from_email': 'Some Event Person <sep@event.com>',
    # List extra fields to add to the mail from the ticket, check ticket_fields for more info.
    'ticket_fields_extra': ['Union Medlems ID'],
    # Names of all the tickets types there should be send to the union.
    # Use the --tickets arguments to list all the tickets type.
    # You can also use the --ticket-and-member-ids argument to se that
    # what ticket types there have already been boughtm, based on the  member_fields variable
    'ticket_type_names': [
      'Union ticket for kits',
      'Union ticket for adults'
    ]
  }]

  # The template for emails.
  # The variable {to_name}, {from_name}, {union_name} & {extra_text} all come from
  # the keys in the above unions variable. You can change the text if you want.
  email_template = (
      "Hej {to_name}\n"
      "\n"
      "Hermed billetter med tilskud fra {union_name}. "
      "Skulle der være solgt {union_name}-billetter til personer der viser sig ikke at være medlem, så må I lige sige til.\n"
      "\n"
      "-= Billet Info =-\n"
      "{ticket_info_text}\n"
      "\n"
      "Mvh. {from_name}\n"
      "{extra_text}")


