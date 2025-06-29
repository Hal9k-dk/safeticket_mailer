# ex: set tabstop=8 softtabstop=0 expandtab shiftwidth=2 smarttab:
from os import environ
from typing import Optional, List


class Union:
    name: str
    subject: str
    to_name: str
    to_email: str
    cc_email: Optional[str]
    from_name: str
    from_email: str
    invoice_subject: str
    invoice_address: str
    invoice_zip_code: str
    invoice_city: str
    extra_text: Optional[str]
    ticket_fields_extra: List[str]
    ticket_type_names: List[str]
    additional_sponsorship: Optional[float]
    invoice_cvr_no: Optional[str]

    def __init__(self, name: str, subject: str, to_name: str, to_email: str,
                 from_name: str, from_email: str, ticket_type_names: List[str],
                 invoice_subject: str, invoice_address: str, invoice_zip_code: str, invoice_city: str,
                 cc_email: Optional[str] = None, extra_text: Optional[str] = None,
                 ticket_fields_extra: List[str] = None, additional_sponsorship: float = None,
                 invoice_cvr_no: Optional[str] = None, invoice_cc_email: Optional[str] = None):
        """
        Fill out the information for the Union
        :param name: Name of the Union
        :param subject: The subject for the status email
        :param to_name: The name of the receiver in the Email Template
        :param to_email: The email-address of the receiver of the email
        :param from_name: The name of the sender in the Email Template
        :param from_email: The email-address of the sender of the email
        :param ticket_type_names: Names of all the tickets types there should be sent to the union.
        Use the --tickets arguments to list all the tickets type.
        You can also use the --ticket-and-member-ids argument to se that
        what ticket types there have already been bought, based on the  member_fields variable
        :param invoice_subject: The subject for the invoice email
        :param invoice_address: The street name and number of receiver's address
        :param invoice_zip_code: The zip code of the receiver's address
        :param invoice_city: The city of the receiver's address
        :param cc_email: The email-address to be CC of the email, can the `None` to disable
        :param extra_text: List extra fields to add to the mail from the ticket, check ticket_fields for
        more info
        :param ticket_fields_extra: List extra fields to add to the mail from the ticket,
        check ticket_fields for more info
        :type additional_sponsorship: How much money the union sponsors additional on top of the tickets
        :type invoice_cvr_no: A CVR (Central Business Register - Denmark) is the number used to identify
        a company in Denmark
        :type invoice_cc_email: Add an email that will get Cc'd the invoice
        """
        self.name = name
        self.subject = subject
        self.to_name = to_name
        self.to_email = to_email
        self.cc_email = cc_email
        self.from_name = from_name
        self.from_email = from_email
        self.invoice_subject = invoice_subject
        self.invoice_address = invoice_address
        self.invoice_zip_code = invoice_zip_code
        self.invoice_city = invoice_city
        self.extra_text = extra_text
        self.ticket_fields_extra = ticket_fields_extra if ticket_fields_extra else []
        self.ticket_type_names = ticket_type_names
        self.additional_sponsorship = additional_sponsorship
        self.invoice_cvr_no = invoice_cvr_no
        self.invoice_cc_email = invoice_cc_email


class Config:
    # Login info for Safeticket.dk
    organization = 'example'  # EXAMPLE.safeticket.dk
    username = environ["SAFETICKET_USERNAME"]  # Normally, this is an email address
    password = environ["SAFETICKET_PASSWORD"]

    # SMTP (mail) server config (currently, only SSL is supported)
    class SMTP:
        host = 'example.com'
        port = 587  # '25, 465, 587'
        username = environ["SMTP_PASSWORD"]
        password = environ["SMTP_PASSWORD"]

    # This variable tells the SafeTicket mailer to send the last status mail X amount of
    # days after the event, this is based on the 'settledate' information.
    # You can find this information but using the --events argument
    send_last_status_mail_days_after_event = 3

    # This variable tells the SafeTicket mailer to send the invoice mail X amount of
    # days after the event, this is based on the 'settledate' information.
    # You can find this information but using the --events argument
    send_invoice_mail_days_after_event = 14 + 3

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
    # A CVR (Central Business Register - Denmark) is the number used to identify a company in Denmark
    invoice_sender_cvr_no = "0000000000"
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

    # The currency use in the invoices
    currency = "DKK"

    # Create a list of all the unions that needs and email and what it should contain
    unions = [
        Union(
            name='Union1',
            subject='Tickets sold so far',
            to_name='Union Person',
            to_email='Some Persen <sp@union.org>',
            from_name='Event Persen',
            from_email='Some Event Person <sep@event.com>',
            ticket_type_names=[
                'Union ticket for kits',
                'Union ticket for adults'
            ],
            invoice_subject="Invoice for sold tickets",
            invoice_address="Street Address and Street Number",
            invoice_zip_code="0000",
            invoice_city="City",
            cc_email=None,
            extra_text='Phone Nr. 8888 8888 ',
            ticket_fields_extra=[
                'Union Medlems ID'
            ],
            additional_sponsorship=1337.00,
        )
    ]

    # The template for the status emails.
    # The variable {to_name}, {from_name}, {union_name}, {extra_text} & {ticket_info_text} all come from
    # the keys in the above unions variable. You can change the text if you want.
    email_template_status = (
        "Hej {to_name}\n"
        "\n"
        "Hermed billetter med tilskud fra {union_name}. "
        "Skulle der være solgt {union_name}-billetter til personer der viser sig ikke at være medlem, "
        "så må I lige sige til.\n"
        "\n"
        "---=== Billet Info ===---\n"
        "{ticket_info_text}\n"
        "\n"
        "Mvh. {from_name}\n"
        "{extra_text}\n"
        "\n"
        "PS Hvis der mangler information eller hvis I har ønsker til hvordan vi gør denne mail bedre, "
        "så vil jeg gøre mit bedste for at efterkomme dem."
    )
    # This message in the `ticket_info_text` field of `email_template_status` if there are no tickets sold
    email_template_status_no_ticket = "Der er ikke blevet solgt nogle billetter endnu"

    # The template for the invoice emails.
    # The variable {to_name}, {from_name}, {event_name}, {union_name} & {extra_text} all come from
    # the keys in the above unions variable. You can change the text if you want.
    email_template_invoice = (
        "Hej {to_name}\n"
        "\n"
        "Vi, I Sommerhack, takker mange gange for støtten fra {union_name}. "
        "{event_name} er ovre og det gik rigtig godt :D\n"
        ""
        "Så som det sidste sender vi jer hermed faktura for dette Sommerhack og vi håber selvfølgelig, "
        "at I vil støtte os igen næste gang :)\n"
        "\n"
        "Mvh. {from_name}\n"
        "{extra_text}\n"
        "\n"
        "PS Hvis der mangler information eller hvis I har ønsker til hvordan vi gør denne mail bedre, "
        "så vil jeg gøre mit bedste for at efterkomme dem."
    )

    # The template for if there are no invoice emails, but just to say thanks.
    # The variable {to_name}, {from_name}, {event_name}, {union_name} & {extra_text} all come from
    # the keys in the above unions variable. You can change the text if you want.
    email_template_no_invoice = (
        "Hej {to_name}\n"
        "\n"
        "Vi, I Sommerhack, takker mange gange for støtten fra {union_name}. "
        "{event_name} er ovre og det gik rigtig godt :D\n"
        ""
        "Vi har (desværre) ingen faktura til jer, da der ikke er blevet solgt nogle billetter til {union_name}. "
        "Vi håber dog stadigvæk, at I vil støtte os igen næste gang ;)\n"
        "\n"
        "Mvh. {from_name}\n"
        "{extra_text}\n"
        "\n"
        "PS Hvis der mangler information eller hvis I har ønsker til hvordan vi gør denne mail bedre, "
        "så vil jeg gøre mit bedste for at efterkomme dem."
    )
