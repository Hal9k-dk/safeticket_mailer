import argparse
import mimetypes
import smtplib
import ssl
import sys
from email.header import Header
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import parseaddr
from io import BytesIO
from typing import List, Dict, Any, NamedTuple

from odf import opendocument
from odf.table import Table, TableRow, TableCell, TableColumn
from odf.style import Style, TableColumnProperties, TableCellProperties, ParagraphProperties

from config import Union, Config


TicketTypesType = Dict[str, List[Dict[str, Any]]]


def args_parser():
    parser = argparse.ArgumentParser(description='SafeTicket Mailer')
    parser.add_argument('--debug', dest='debug', action='store_true',
                        default=False, help='Print a lot of info')

    parser.add_argument('--events', dest='events', action='store_true',
                        default=False, help='Print all events')
    parser.add_argument('--tickets', dest='tickets', action='store_true',
                        default=False, help='Print all the types of ticket of an event')
    parser.add_argument('--ticket-fields', dest='ticket_fields', action='store_true',
                        default=False, help='Print all the possible fields existing for the tickets')
    parser.add_argument('--ticket-stats', dest='ticket_stats', action='store_true',
                        default=False, help='Print ticket types and there stats for the event')
    parser.add_argument('--use-manual-ticket', '--generate-manual-ticket-template',
                        dest='manual_ticket', action='store_true',
                        default=False, help='Generate template yaml-file and folder structure for manual tickets')
    parser.add_argument('--show-emails', dest='show_emails', action='store_true',
                        default=False, help='Display the email there is going to be sendt')
    parser.add_argument('--send-emails', dest='send_emails', action='store_true',
                        default=False, help='This will send the emails to the unions')
    parser.add_argument('--overwrite-email-receiver', dest='overwrite_email_receiver',
                        default=None, help='This is for testing. It makes it so that only this email receive anything')
    parser.add_argument('--generate-invoice', dest="generate_invoice", default=None,
                        help="Select the path for there to dump the generated invoices")
    parser.add_argument('--send-invoice', dest="send_invoice", action='store_true', default=False,
                        help="Send an invoice to all the unions that need one")

    parser_past = parser.add_mutually_exclusive_group()
    parser_past.add_argument('--past', dest='past', action='store_true',
                             default=False, help='Find events from the past')
    parser_past.add_argument('--auto-include-past', dest='auto_include_past', action='store_true',
                             default=False, help='Find events from the past')

    # Print --help message if now arguments
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    return parser.parse_args()


class MemoryFile(NamedTuple):
    filename: str
    data: bytes


def create_spreadsheet_ticket_data(union: Union, ticket_types: TicketTypesType, config: Config) -> MemoryFile:
    _width_in_cm = 2.64
    _number_characters = 12
    _average_character_length_in_cm = _width_in_cm / _number_characters

    columns = config.ticket_fields + union.ticket_fields_extra

    doc = opendocument.OpenDocumentSpreadsheet()
    table_all = Table(name='all', stylename="table=all")

    union_tickets = sum([ticket for ticket_name, ticket in ticket_types.items()
                         if ticket_name in union.ticket_type_names], [])
    for index, column in enumerate(columns):
        style_name = f"{table_all.getAttribute('stylename')}|column={index+1}"
        table_column = TableColumn(stylename=style_name)
        table_all.addElement(table_column)

        calc_length_in_cm = max(
            [len(union_ticket[columns[index]])
             for union_ticket in union_tickets
             if union_ticket.get("Ordre") != "manual-ticket"] + [len(column)]
        ) * _average_character_length_in_cm + 0.2

        style = Style(name=style_name, family=table_column.qname[1])
        style.addElement(TableColumnProperties(columnwidth=f"{calc_length_in_cm:0.2f}cm"))
        doc.automaticstyles.addElement(style)

    for header_index, ticket_type_name in enumerate(union.ticket_type_names):
        ticket_type = ticket_types[ticket_type_name]

        if ticket_type:
            row_ticket_name = TableRow()

            style_name = f"{table_all.getAttribute('stylename')}|header={header_index + 1}"
            cell_ticket_name = TableCell(
                stylename=style_name,
                stringvalue=ticket_type_name, valuetype="string",
                numbercolumnsspanned=columns.__len__(),
            )
            style = Style(name=style_name, family=cell_ticket_name.qname[1])
            style.addElement(ParagraphProperties(textalign="center"))
            doc.automaticstyles.addElement(style)

            row_ticket_name.addElement(cell_ticket_name)
            table_all.addElement(row_ticket_name)

            row_header = TableRow()
            for column_index, column in enumerate(columns):
                style_name = f"{table_all.getAttribute('stylename')}|column={column_index+1}|header={header_index + 1}"
                row_header.addElement(
                    TableCell(
                        stylename=style_name,
                        stringvalue=column, valuetype="string",
                    )
                )
                style = Style(name=style_name, family=cell_ticket_name.qname[1])
                style.addElement(TableCellProperties(borderbottom="0.74pt groove #000000"))
                doc.automaticstyles.addElement(style)
            table_all.addElement(row_header)

            for ticket in ticket_type:
                row_sold_ticket = TableRow()
                for column in columns:
                    row_sold_ticket.addElement(
                        TableCell(
                            formula='''="{}"'''.format(ticket[column]),
                        )
                    )
                table_all.addElement(row_sold_ticket)

            for _ in range(2):
                table_all.addElement(TableRow())

    doc.spreadsheet.addElement(table_all)

    doc.save('/tmp/test.ods')

    data = BytesIO()
    doc.write(data)
    data.seek(0)

    return MemoryFile(filename="tickets sold.ods", data=data.read())


def show_email(msg: str, union: Union, subject: str, cc_emails: List[str],
               attachment: MemoryFile = None):
    cc_emails = cc_emails if cc_emails else []

    print('\n============(Mail - {})============'.format(union.name))
    print('TO:         {}'.format(union.to_email))
    for cc_email in cc_emails:
        if cc_email:
            print('CC:         {}'.format(cc_email))
    print('FROM:       {}'.format(union.from_email))
    print('SUBJECT:    {}'.format(subject))
    if attachment:
        print('Attachment: {}'.format(attachment.filename))
    print('\n---------------------------')
    print(msg)


# This is need because there is a bug in MIMEText
def encode_email_address_name(email_address: str) -> str:
    (name, address) = parseaddr(email_address)
    return '{} <{}>'.format(Header(name).encode('utf-8'), address)


def send_email(
        msg: str,
        union: Union,
        cc_emails: List[str],
        bcc_emails: List[str],
        config: Config,
        attachment: MemoryFile = None,
        overwrite_email_receiver: str = None,
):
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(config.SMTP.host, config.SMTP.port, context=context) as smtpObj:
        email = MIMEMultipart()
        email.attach(MIMEText(msg))
        email['To'] = encode_email_address_name(union.to_email)
        if union.cc_email:
            email['CC'] = ', '.join([encode_email_address_name(cc_email) for cc_email in cc_emails if cc_email])
        email['From'] = encode_email_address_name(union.from_email)
        email['Subject'] = union.subject

        if attachment:
            _type, _encoding = mimetypes.guess_type(url=attachment.filename)
            email.attach(MIMEApplication(
                _data=attachment.data,
                _subtype="octet-stream" if _type is None else _type.split("/")[-1],
                name=attachment.filename,
            ))

        smtpObj.login(config.SMTP.username, config.SMTP.password)

        # Make sure we only get the address and not the name
        receivers = [parseaddr(union.to_email)[1]]

        if cc_emails:
            receivers.extend([parseaddr(cc_email)[1] for cc_email in cc_emails if cc_email])

        if bcc_emails:
            receivers.extend([parseaddr(bcc_email)[1] for bcc_email in bcc_emails if bcc_emails])

        smtpObj.sendmail(
            from_addr=union.from_email,
            to_addrs=[overwrite_email_receiver] if overwrite_email_receiver else receivers,
            msg=email.as_string()
        )
