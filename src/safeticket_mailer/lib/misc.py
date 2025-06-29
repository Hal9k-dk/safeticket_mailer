import argparse
import mimetypes
import re
import smtplib
import ssl
import sys
import io
from pathlib import Path
from email.header import Header
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import parseaddr
from typing import List, Dict, Any, NamedTuple

try:
    from odf import opendocument
    from odf.table import Table, TableRow, TableCell, TableColumn
    from odf.style import Style, TableColumnProperties, TableCellProperties, ParagraphProperties
except ModuleNotFoundError:
    print("You need to install odfpy to use this module: python3 -m pip install odfpy")
    sys.exit(1)


from .config import __file__ as config_example_file


TicketTypesType = Dict[str, List[Dict[str, Any]]]


def args_parser():
    parser = argparse.ArgumentParser(description='SafeTicket Mailer')
    parser.add_argument('--debug', dest='debug', action='store_true',
                        default=False, help='Print a lot of info')

    parser.add_argument('--config-file', '--config', dest='config_file', type=Path, required=True,
                        help="Path to the config.py file, which is based on the example file: {}".format(
                            Path(config_example_file).parent.joinpath("config_example.py")
                        ))
    parser.add_argument('--data-folder', dest='data_folder', type=Path, required=True,
                        help="The data folder. Tracking of which emails have been sendt is stored here.")

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


class RowNumber():
    _number: int
    def __init__(self):
        self._number = 0

    def get(self) -> int:
        self._number += 1
        return self._number


def create_spreadsheet_grouped_by_ticket_type_data(union, ticket_types: TicketTypesType, config) -> MemoryFile:
    _width_in_cm = 2.64
    _number_characters = 12
    _average_character_length_in_cm = _width_in_cm / _number_characters

    column_names = config.ticket_fields + union.ticket_fields_extra

    doc = opendocument.OpenDocumentSpreadsheet()
    table_all = Table(name='all', stylename="table=all")

    union_tickets = sum([ticket for ticket_name, ticket in ticket_types.items()
                         if ticket_name in union.ticket_type_names], [])
    for index, column in enumerate(column_names):
        style_name = f"{table_all.getAttribute('stylename')}|column={index+1}"
        table_column = TableColumn(stylename=style_name)
        table_all.addElement(table_column)

        calc_length_in_cm = max(
            [len(union_ticket[column_names[index]])
             for union_ticket in union_tickets
             if union_ticket.get("Ordre") != "manual-ticket"] + [len(column)]
        ) * _average_character_length_in_cm + 0.2

        style = Style(name=style_name, family=table_column.qname[1])
        style.addElement(TableColumnProperties(columnwidth=f"{calc_length_in_cm:0.2f}cm"))
        doc.automaticstyles.addElement(style)

    for header_index, ticket_type_name in enumerate(union.ticket_type_names):
        tickets = ticket_types[ticket_type_name]

        if tickets:
            row_ticket_name = TableRow()

            style_name = f"{table_all.getAttribute('stylename')}|header={header_index + 1}"
            cell_ticket_name = TableCell(
                stylename=style_name,
                stringvalue=ticket_type_name, valuetype="string",
                numbercolumnsspanned=column_names.__len__(),
            )
            style = Style(name=style_name, family=cell_ticket_name.qname[1])
            style.addElement(ParagraphProperties(textalign="center"))
            doc.automaticstyles.addElement(style)

            row_ticket_name.addElement(cell_ticket_name)
            table_all.addElement(row_ticket_name)

            row_header = TableRow()
            for column_index, column in enumerate(column_names):
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

            for ticket in tickets:
                ticket_row = TableRow()
                for header_column in column_names:
                    value = ticket[header_column]
                    if re.search(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}$", value):
                        ticket_row.addElement(TableCell(
                            datevalue=value, valuetype="date",
                        ))

                    elif re.search(r"^[0-9]+$", value):
                        ticket_row.addElement(TableCell(
                            value=value, valuetype="float",
                        ))

                    else:
                        ticket_row.addElement(TableCell(
                            stringvalue=value, valuetype="string",
                        ))

                table_all.addElement(ticket_row)

            for _ in range(2):
                table_all.addElement(TableRow())

    doc.spreadsheet.addElement(table_all)

    doc.save(f"/tmp/grouped-by-type.{union.name}.ods")

    data = io.BytesIO()
    doc.write(data)
    data.seek(0)

    return MemoryFile(filename="tickets-sold_grouped-by-type.ods", data=data.read())


def order_ticket_types(ticket: Dict[str, Any]) -> int:
    value = 0
    if 'Voksen' in ticket['Billettype']:
        value += 100
    if 'Alle dage' in ticket['Billettype']:
        value += 10
    return value

def add_cell_format_in_correct_format(row: TableRow, value: str):
    if re.search(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}$", value):
        row.addElement(TableCell(
            datevalue=value, valuetype="date",
        ))

    elif re.search(r"^[0-9]+$", value):
        row.addElement(TableCell(
            value=value, valuetype="float",
        ))

    else:
        row.addElement(TableCell(
            stringvalue=value, valuetype="string",
        ))

def create_spreadsheet_grouped_by_buyer_data(union, ticket_types: TicketTypesType, config) -> MemoryFile:
    _width_in_cm = 2.63
    _number_characters = 12
    _average_character_length_in_cm = _width_in_cm / _number_characters

    column_names_ticket_fields = ["Billettype"] + config.ticket_fields
    column_names = column_names_ticket_fields + union.ticket_fields_extra

    doc = opendocument.OpenDocumentSpreadsheet()
    table_all = Table(name='all', stylename="table=all")


    union_tickets = sum([ticket for ticket_name, ticket in ticket_types.items()
                         if ticket_name in union.ticket_type_names], [])
    for index, column in enumerate(column_names):
        style_name = f"{table_all.getAttribute('stylename')}|column={index+1}"
        table_column = TableColumn(stylename=style_name)
        table_all.addElement(table_column)

        calc_length_in_cm = max(
            [len(union_ticket[column_names[index]])
             for union_ticket in union_tickets
             if union_ticket.get("Ordre") != "manual-ticket"] + [len(column)]
        ) * _average_character_length_in_cm + 0.2

        style = Style(name=style_name, family=table_column.qname[1])
        style.addElement(TableColumnProperties(columnwidth=f"{calc_length_in_cm:0.2f}cm"))
        doc.automaticstyles.addElement(style)

    group_by_buyer = {}
    for ticket_type_name in union.ticket_type_names:
        tickets = ticket_types[ticket_type_name]
        for ticket in tickets:
            group_by_buyer.setdefault(ticket["Ordre"], [])
            group_by_buyer[ticket["Ordre"]].append(ticket)
    for ordre_index in group_by_buyer:
        group_by_buyer[ordre_index].sort(key=order_ticket_types, reverse=True)


    header_index = 0
    style_family = "table-cell"
    style_name = f"{table_all.getAttribute('stylename')}|header={header_index + 1}"
    style = Style(name=style_name, family=style_family)
    style.addElement(ParagraphProperties(textalign="center"))
    doc.automaticstyles.addElement(style)

    row_header = TableRow()
    for column_index, column in enumerate(column_names):
        style_name = f"{table_all.getAttribute('stylename')}|column={column_index+1}|header={header_index + 1}"
        row_header.addElement(
            TableCell(
                stylename=style_name,
                stringvalue=column, valuetype="string",
            )
        )
        style = Style(name=style_name, family=style_family)
        style.addElement(TableCellProperties(borderbottom="0.74pt groove #000000"))
        doc.automaticstyles.addElement(style)
    table_all.addElement(row_header)

    for ticket_order, tickets in group_by_buyer.items():
        for ticket_index, ticket in enumerate(tickets):
            if ticket_index == 0:
                ticket_row = TableRow()
                for header_column in column_names:
                    value = ticket[header_column]
                    add_cell_format_in_correct_format(row=ticket_row, value=value)

                table_all.addElement(ticket_row)

            else:
                ticket_row = TableRow()
                for header_column in column_names_ticket_fields:
                    add_cell_format_in_correct_format(row=ticket_row, value=ticket[header_column])
                table_all.addElement(ticket_row)

        row_sum = TableRow()
        row_sum.addElement(TableCell(
            stylename=style_name,
            stringvalue=f"Antal billetter købt: {len(tickets)}", valuetype="string",
        ))
        table_all.addElement(row_sum)

        for _ in range(1):
            table_all.addElement(TableRow())

    doc.spreadsheet.addElement(table_all)

    doc.save(f"/tmp/grouped-by-buyer.{union.name}.ods")

    data = io.BytesIO()
    doc.write(data)
    data.seek(0)

    return MemoryFile(filename="tickets-sold_grouped-by-buyer.ods", data=data.read())


def show_email(msg: str, union, subject: str, cc_emails: List[str],
               attachments: List[MemoryFile] = None):
    cc_emails = cc_emails if cc_emails else []

    print('\n============(Mail - {})============'.format(union.name))
    print('TO:         {}'.format(union.to_email))
    for cc_email in cc_emails:
        if cc_email:
            print('CC:         {}'.format(cc_email))
    print('FROM:       {}'.format(union.from_email))
    print('SUBJECT:    {}'.format(subject))
    if attachments:
        for attachment in attachments:
            print('Attachment: {}'.format(attachment.filename))
    print('\n---------------------------')
    print(msg)


# This is need because there is a bug in MIMEText
def encode_email_address_name(email_address: str) -> str:
    (name, address) = parseaddr(email_address)
    return '{} <{}>'.format(Header(name).encode('utf-8'), address)


def send_email(
        msg: str,
        union,
        cc_emails: List[str],
        bcc_emails: List[str],
        config,
        attachments: List[MemoryFile] = None,
        overwrite_email_receiver: str = None,
):
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(config.SMTP.host, config.SMTP.port, context=context) as smtpObj:
        email = MIMEMultipart()
        email.attach(MIMEText(msg))
        email['To'] = encode_email_address_name(union.to_email)

        if union.cc_email:
            union_cc_email = [union.cc_email]
        else:
            union_cc_email = []
        merged_cc_emails = list(set(union_cc_email + cc_emails))

        if merged_cc_emails:
            email['CC'] = ', '.join([encode_email_address_name(cc_email)
                                     for cc_email in merged_cc_emails
                                     if cc_email])
        email['From'] = encode_email_address_name(union.from_email)
        email['Subject'] = union.subject

        if attachments:
            for attachment in attachments:
                _type, _encoding = mimetypes.guess_type(url=attachment.filename)
                email.attach(MIMEApplication(
                    _data=attachment.data,
                    _subtype="octet-stream" if _type is None else _type.split("/")[-1],
                    name=attachment.filename,
                ))

        smtpObj.login(config.SMTP.username, config.SMTP.password)

        # Make sure we only get the address and not the name
        receivers = [parseaddr(union.to_email)[1]]

        if merged_cc_emails:
            receivers.extend([parseaddr(cc_email)[1] for cc_email in merged_cc_emails if cc_email])

        if bcc_emails:
            receivers.extend([parseaddr(bcc_email)[1] for bcc_email in bcc_emails if bcc_emails])

        smtpObj.sendmail(
            from_addr=union.from_email,
            to_addrs=[overwrite_email_receiver] if overwrite_email_receiver else receivers,
            msg=email.as_string()
        )
