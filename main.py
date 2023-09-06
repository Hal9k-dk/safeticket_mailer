#!/usr/bin/env python3
# ex: set tabstop=8 softtabstop=0 expandtab shiftwidth=2 smarttab:
import json
import re
import sys
from datetime import datetime, timedelta, date, timezone
from io import StringIO
from csv import DictReader
from pathlib import Path
from pprint import pprint as pp
from typing import List

import yaml
from tabulate import tabulate

from lib.invoice import Invoice, TicketInfo
from lib.misc import args_parser, show_email, send_email, TicketTypesType, create_spreadsheet_ticket_data, MemoryFile
from lib.safeticket_wrapper import SafeTicket
from config import Config

CONFIG = Config()


def main():
    args = args_parser()

    safe_ticket = SafeTicket(
        CONFIG.organization,
        CONFIG.username,
        CONFIG.password)

    if safe_ticket.login() is False:
        print("Something when wrong with login")
        exit(1)

    var_folder_path = Path(__file__).parent.joinpath("var")
    var_event_folder_path = var_folder_path.joinpath(CONFIG.event_name)
    var_event_run_folder_path = var_event_folder_path.joinpath("progress_status")
    var_event_run_folder_path.mkdir(parents=True, exist_ok=True)

    sent_invoice_mail_path = var_event_run_folder_path.joinpath("sent-invoice-mail.json")
    if not sent_invoice_mail_path.is_file():
        sent_invoice_mail_path.write_text(json.dumps([], indent=4))

    sent_last_status_mail_path = var_event_run_folder_path.joinpath("sent-last-status-mail.json")
    if not sent_last_status_mail_path.is_file():
        sent_last_status_mail_path.write_text(json.dumps([], indent=4))

    sent_status_mail_path = var_event_run_folder_path.joinpath("sent-status-mail.json")
    if not sent_status_mail_path.is_file():
        sent_status_mail_path.write_text(json.dumps({}, indent=4))

    # Look through all the events and find the one we need
    events = safe_ticket.get_events(past=args.past)

    if args.auto_include_past is True and args.past is False:
        _past_events = safe_ticket.get_events(past=True)
        events.data.events += _past_events.data.events

    if args.events or args.debug:
        print(yaml.safe_dump([e.__dict__ for e in events.data.events]))

    _event = [event for event in events.data.events
              if event.name == CONFIG.event_name]
    if len(_event) == 1:
        event = _event[0]
    else:
        print('There was no event for the name "{}", try the --events args.'.format(CONFIG.event_name),
              file=sys.stderr)
        sys.exit(2)

    # Get all the data about ticket types from the selected `event`
    tickets = safe_ticket.get_event_tickets(event.id)

    # Filter the ticket types IDs into a list
    ticket_ids = []

    # Contains all the ticket types and how many there have been sold of them
    ticket_types: TicketTypesType = {}
    for ticket in tickets.data.tickets:
        ticket_ids.append(ticket.id)
        ticket_types[ticket.name] = []

    # Export ticket stats from the event into a CSV file
    csv_content = safe_ticket.export_tickets_stats(event.id, ticket_ids)

    # Parse the CSV file
    _csv_reader = DictReader(
        StringIO(csv_content),
        skipinitialspace=True,
        delimiter=';',
        quotechar='"')

    # Doing counting of the tickets
    for row in _csv_reader:
        ticket_types[row['Billettype']].append(row)

    if args.manual_ticket:
        manual_ticket_template_filename = "manual-ticket-template.yaml"
        var_event_manual_ticket_folder_path = var_event_folder_path.joinpath("manual-ticket")
        var_event_manual_ticket_folder_path.mkdir(parents=True, exist_ok=True)

        default_attributes = {'Ordre': "manual-ticket", 'Arrangement': event.name,
                              'Betalingstype': "Cash/MobilePay", 'Status': "Betalt"}

        manual_ticket_all_fields = {
            **{field_name: '' for field_name in _csv_reader.fieldnames},
            'Tidspunkt': datetime.fromtimestamp(event.event_ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
            **default_attributes,
        }
        manual_ticket_all_fields.pop('Billetnummer')
        manual_ticket_all_fields.pop('Ankommet')
        manual_ticket_all_fields.pop('Ankomst')
        manual_ticket_all_fields.pop('Sektion')

        manual_ticket_template_content = (
            '# List of all the ticket types (Billettype) there are. \n'
            '# Please, copy & paste the one you bought with the question mark (")\n'
            '#\n'
            '{list_of_ticket_types}\n'
            '\n'
            '{list_of_fields_in_the_ticket}'
        ).format(
            list_of_ticket_types='\n'.join([f'# "{ticket_name}"' for ticket_name in sorted(ticket_types.keys())]),
            list_of_fields_in_the_ticket=yaml.safe_dump(manual_ticket_all_fields).replace("'", '"')
        )

        with open(var_event_folder_path.joinpath(manual_ticket_template_filename), "w") as f:
            f.write(manual_ticket_template_content)

        for manual_ticket in var_event_manual_ticket_folder_path.iterdir():
            if manual_ticket.suffix.lower() not in ['.yaml', '.yml']:
                continue

            with open(manual_ticket) as f:
                manual_ticket_data = {**yaml.safe_load(f), **default_attributes}

            if manual_ticket_data["Billettype"] in ticket_types:
                manual_ticket_data["Billetnummer"] = manual_ticket.name
                ticket_types[manual_ticket_data["Billettype"]].append(manual_ticket_data)
            else:
                print(f"The ticket type (Billettype) is wrong in the ticket: {manual_ticket}")
                exit(1)

    if args.tickets or args.debug:
        print('\n============(All The Tickets Types)============')
        pp(sorted(ticket_types.keys()))
    if args.ticket_fields or args.debug:
        print('\n===(All The Possible Fields of The Tickets)====')
        pp(sorted(_csv_reader.fieldnames))
    if args.ticket_stats or args.debug:
        print('\n================(Ticket Stats - Total: {})================='.format(
            sum(map(lambda x: len(x), ticket_types.values()))))
        pp([{k: len(v)} for k, v in ticket_types.items()])

    for index, union in enumerate(CONFIG.unions):
        fields = CONFIG.ticket_fields + union.ticket_fields_extra
        ticket_info_text = []
        for ticket_type_name in union.ticket_type_names:
            try:
                if ticket_types[ticket_type_name]:
                    data = []
                    for ticket in ticket_types[ticket_type_name]:
                        data.append([ticket[field] for field in fields])

                    ticket_info_text.append('{}:\n{}\nAntal billet solgt: {}'.format(
                        ticket_type_name,
                        tabulate(data, headers=fields),
                        len(ticket_types[ticket_type_name]),
                    ))
            except KeyError as e:
                print("ERROR: The fields {} doesn't exist, "
                      "check the variable 'ticket_fields' in the config.py file".format(e))
                sys.exit(1)

        msg_status = CONFIG.email_template_status.format(
            to_name=union.to_name,
            from_name=union.from_name,
            union_name=union.name,
            ticket_info_text=(
                '\n\n'.join(ticket_info_text) if ticket_info_text else CONFIG.email_template_status_no_ticket
            ),
            extra_text=union.extra_text)

        memory_file_status = (create_spreadsheet_ticket_data(union=union, ticket_types=ticket_types, config=CONFIG)
                              if ticket_info_text else None)
        if args.show_emails or args.debug:
            if not union.ticket_type_names:
                print("============(Mail - {})============".format(union.name))
                print(f"Info: No status email was created for the union: {union.name}")
                print(f"Reason: There are not set any ticket (ticket_type_names) in the config file for the union")
                continue

            show_email(msg=msg_status, union=union,
                       subject=union.invoice_subject, cc_emails=[union.cc_email],
                       attachment=memory_file_status)

        if args.send_emails:
            if not union.ticket_type_names:
                print(f"No status email was sent to {union.name}, "
                      f"because there are not set any ticket (ticket_type_names) in the config file for the union")
                continue

            if datetime.strptime(event.settle_date, "%d.%m.%Y").date() + timedelta(
                    days=Config.send_last_status_mail_days_after_event) <= date.today():

                send_last_status_update: List[str] = json.loads(sent_last_status_mail_path.read_text())
                if union.name in send_last_status_update:
                    print(f'============(The last status email was already sent to {union.name})============')
                else:
                    send_email(msg=msg_status, union=union, cc_emails=[union.cc_email],
                               bcc_emails=[union.cc_email], attachment=memory_file_status,
                               config=CONFIG, overwrite_email_receiver=args.overwrite_email_receiver)
                    send_last_status_update.append(union.name)
                    sent_last_status_mail_path.write_text(json.dumps(send_last_status_update, indent=4))
            else:
                sent_status_update = json.loads(sent_status_mail_path.read_text())
                send_email(msg=msg_status, union=union, cc_emails=[union.cc_email],
                           bcc_emails=[], attachment=memory_file_status,
                           config=CONFIG, overwrite_email_receiver=args.overwrite_email_receiver)
                sent_status_update.setdefault(union.name, [])
                sent_status_update[union.name].append(datetime.utcnow().isoformat())
                sent_status_mail_path.write_text(json.dumps(sent_status_update, indent=4))

        if args.send_invoice:
            args.generate_invoice = '/tmp/safe_ticket'
            Path(args.generate_invoice).mkdir(0o700, parents=True, exist_ok=True)

        memory_file_invoice = None
        if args.generate_invoice:
            _tickets = {}
            for ticket_type_name in union.ticket_type_names:
                _all_ticket_of_one_type = ticket_types[ticket_type_name]
                if _all_ticket_of_one_type:
                    price: str = _all_ticket_of_one_type[0]['Pris']
                    _tickets[ticket_type_name] = TicketInfo(
                        selling_price=float(price.replace('.', '').replace(',', '.')),
                        discount_percent=int(re.search(r'(\d+) *%', ticket_type_name).group(1)),
                        sold_tickets=len(_all_ticket_of_one_type),
                    )

            folder = Path(args.generate_invoice).resolve()
            invoice = Invoice(
                title=CONFIG.event_name,
                invoice_no=index + 1,
                invoice_no_prefix=CONFIG.invoice_no_prefix,
                sender_name=CONFIG.invoice_sender_name,
                sender_cvr_no=CONFIG.invoice_sender_cvr_no,
                sender_email=CONFIG.invoice_contact_email,
                from_address=CONFIG.invoice_sender_address,
                from_zip_code=CONFIG.invoice_sender_zip_code,
                from_city=CONFIG.invoice_sender_city,
                receiver_name=union.name,
                receiver_cvr_no=union.invoice_cvr_no,
                to_address=union.invoice_address,
                to_zip_code=union.invoice_zip_code,
                to_city=union.invoice_city,
                registration_no=CONFIG.invoice_registration_no,
                account_no=CONFIG.invoice_account_no,
            )

            pdf_file_path = folder.joinpath("{}.pdf".format(re.sub(r'[^\w ]', '', union.name)))
            send_invoice = invoice.generate_html(
                pdf_output_file=pdf_file_path,
                additional_sponsorship=union.additional_sponsorship,
                currency=CONFIG.currency,
                tickets=_tickets,
            )

            if send_invoice:
                memory_file_invoice = MemoryFile(filename=pdf_file_path.name, data=pdf_file_path.read_bytes())

        if memory_file_invoice:
            msg_invoice = CONFIG.email_template_invoice.format(
                to_name=union.to_name,
                from_name=union.from_name,
                event_name=CONFIG.event_name,
                union_name=union.name,
                extra_text=union.extra_text)
        else:
            msg_invoice = CONFIG.email_template_no_invoice.format(
                to_name=union.to_name,
                from_name=union.from_name,
                event_name=CONFIG.event_name,
                union_name=union.name,
                extra_text=union.extra_text)

        if args.generate_invoice or args.debug:
            _tmp_memory_file = None
            if memory_file_invoice:
                _tmp_memory_file = MemoryFile(filename=f"{args.generate_invoice}/{memory_file_invoice.filename}",
                                              data=memory_file_invoice.data)
            show_email(msg=msg_invoice, union=union,
                       subject=union.invoice_subject, cc_emails=[union.cc_email, CONFIG.invoice_cc_email],
                       attachment=_tmp_memory_file)

        if args.send_invoice:
            if datetime.strptime(event.settle_date, "%d.%m.%Y").date() + timedelta(
                    days=Config.send_invoice_mail_days_after_event) <= date.today():

                sent_invoice_mail: List[str] = json.loads(sent_invoice_mail_path.read_text())
                if union.name in sent_invoice_mail:
                    print(f'The invoice email was already sent to {union.name}')
                else:
                    send_email(msg=msg_invoice, union=union, cc_emails=[union.cc_email, CONFIG.invoice_cc_email],
                               bcc_emails=[union.from_email], attachment=memory_file_invoice,
                               config=CONFIG, overwrite_email_receiver=args.overwrite_email_receiver)
                    sent_invoice_mail.append(union.name)
                    sent_invoice_mail_path.write_text(json.dumps(sent_invoice_mail, indent=4))


if __name__ == '__main__':
    main()
