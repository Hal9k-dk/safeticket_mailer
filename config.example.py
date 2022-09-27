# ex: set tabstop=8 softtabstop=0 expandtab shiftwidth=2 smarttab:
from typing import Optional, List


class Union:
    name: str
    subject: str
    to_name: str
    to_email: str
    cc_email: Optional[str]
    from_name: str
    from_email: str
    invoice_sender_address: str
    invoice_sender_zip_code: str
    invoice_sender_city: str
    extra_text: Optional[str]
    ticket_fields_extra: List[str]
    ticket_type_names: List[str]

    def __init__(self, name: str, subject: str, to_name: str, to_email: str,
                 from_name: str, from_email: str, ticket_type_names: List[str],
                 invoice_sender_address: str, invoice_sender_zip_code: str, invoice_sender_city: str,
                 cc_email: Optional[str] = None, extra_text: Optional[str] = None,
                 ticket_fields_extra: List[str] = None):
        """
        Fill out the information for the Union
        :param name: Name of the Union
        :param subject: Subject of The Email
        :param to_name: The name of the receiver in the Email Template
        :param to_email: The email-address of the receiver of the email
        :param from_name: The name of the sender in the Email Template
        :param from_email: The email-address of the sender of the email
        :param ticket_type_names: Names of all the tickets types there should be sent to the union.
        Use the --tickets arguments to list all the tickets type.
        You can also use the --ticket-and-member-ids argument to se that
        what ticket types there have already been boughtm, based on the  member_fields variable
        :param invoice_sender_address: The street name and number of receiver's address
        :param invoice_sender_zip_code: The zip code of the receiver's address
        :param invoice_sender_city: The city of the receiver's address
        :param cc_email: The email-address to be CC of the email, can the `None` to disable
        :param extra_text: List extra fields to add to the mail from the ticket, check ticket_fields for more info
        :param ticket_fields_extra: List extra fields to add to the mail from the ticket,
        check ticket_fields for more info
        """
        self.name = name
        self.subject = subject
        self.to_name = to_name
        self.to_email = to_email
        self.cc_email = cc_email
        self.from_name = from_name
        self.from_email = from_email
        self.invoice_sender_address = invoice_sender_address
        self.invoice_sender_zip_code = invoice_sender_zip_code
        self.invoice_sender_city = invoice_sender_city
        self.extra_text = extra_text
        self.ticket_fields_extra = ticket_fields_extra if ticket_fields_extra else []
        self.ticket_type_names = ticket_type_names


class Config:
    # Login info for Safeticket.dk
    organization = 'example'  # EXAMPLE.safeticket.dk
    username = 'someone'  # Normally, this is an email address
    password = 'secret'

    # SMTP (mail) server config (currently, only SSL is supported)
    class SMTP:
        host = 'example.com'
        port = 587  # '25, 465, 587'
        username = 'someone'
        password = 'secret'

    # This variable tells the SafeTicket mailer to now send emails X amount of
    # days after the event, this is based on the 'settledate' information.
    # You can find this information but using the --events argument
    extra_days_to_send_emails = 5

    # List events with the --events argument
    # Select the event
    event_name = 'the name of the event'  # Example: "SummerHack 2020"

    # List fields from the ticket to include in the mail when listing ticket soldt.
    # The --ticket-fields argument will list all possible fields.
    ticket_fields = ['Navn', 'Email', 'Addresse', 'Addresse2']

    # The text to prefix the invoice generated number (generated number is a combination of the year
    # and the union number).
    invoice_no_prefix = "EVENT"
    # The name of the sender, which is going to apper on the invoice
    invoice_sender_name = "The name of the sender"
    # Person to contact in case something is wrong with the invoice
    invoice_contact_email = "Person to contact <contact@example.com>"
    # Add an email that will get Cc'd the invoice
    invoice_cc_email = "CC person on the Invoice <cc@example.com>"
    # The street name and number of sender's address
    invoice_sender_address = "Street Name and Street number"
    # The zip code of the sender's address
    invoice_sender_zip_code = "1337"
    # The city of the sender's address
    invoice_sender_city = "City"

    # The account registration number for there to transfer money
    invoice_registration_no = "0000"
    # The account number for there to transfer money
    invoice_account_no = "0000000"

    # Create a list of all the unions that needs and email and what it should contain
    unions = [
        Union(
            name='Union1',
            subject='Ticket solgt so far',
            to_name='Union Person',
            to_email='Some Persen <sp@union.org>',
            from_name='Event Persen',
            from_email='Some Event Person <sep@event.com>',
            ticket_type_names=[
                'Union ticket for kits',
                'Union ticket for adults'
            ],
            invoice_sender_address="Street Address and Street Number",
            invoice_sender_zip_code="0000",
            invoice_sender_city="City",
            cc_email=None,
            extra_text='Phone Nr. 8888 8888 ',
            ticket_fields_extra=[
                'Union Medlems ID'
            ]
        )
    ]

    # The template for emails.
    # The variable {to_name}, {from_name}, {union_name} & {extra_text} all come from
    # the keys in the above unions variable. You can change the text if you want.
    email_template = (
        "Hej {to_name}\n"
        "\n"
        "Hermed billetter med tilskud fra {union_name}. "
        "Skulle der være solgt {union_name}-billetter til personer der viser sig ikke at være medlem, så må I lige sige til.\n"
        "\n"
        "---=== Billet Info ===---\n"
        "{ticket_info_text}\n"
        "\n"
        "Mvh. {from_name}\n"
        "{extra_text}\n"
        "\n"
        "PS Hvis der mangler information eller hvis I ønsker på en anden må så skrive, så vil jeg gøre mit bedste for at efter komme det")
