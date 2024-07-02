import html
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from subprocess import Popen, PIPE
from typing import Optional, NamedTuple, Dict, List
import locale

from jinja2 import Template, StrictUndefined

CURRENT_DIR = Path(__file__).parent
TWEMOJI_JS_FILE_PATH = CURRENT_DIR.joinpath("twemoji/twemoji.js")
TEMPLATE_CONTENT = CURRENT_DIR.joinpath("template.html").read_text()


# Check if wkhtmltopdf is installed
BIN_HTML_TO_PDF = "wkhtmltopdf"
if shutil.which(BIN_HTML_TO_PDF) is None:
    print(f"The program `{BIN_HTML_TO_PDF}` localed in the paths from the environment variable PATH "
          f"(os.environ.get('PATH')). You can install `{BIN_HTML_TO_PDF}` with: pikaur -Sy --noconfirm wkhtmltopdf")
    sys.exit(1)


class TicketInfo(NamedTuple):
    selling_price: float
    discount_percent: float
    sold_tickets: int


class Order(NamedTuple):
    count: int
    name: str
    price_formatted: str


class Invoice:
    _template: TEMPLATE_CONTENT

    title: str
    invoice_no: int
    invoice_no_prefix: str

    sender_name: str
    sender_cvr_no: str
    sender_email: str

    from_address: str
    from_zip_code: str
    from_city: str

    receiver_name: str
    to_address: str
    to_zip_code: str
    to_city: str

    registration_no: int
    account_no: int

    def __init__(self, title: str, invoice_no: int, invoice_no_prefix: str,
                 sender_name: str, sender_cvr_no: str, sender_email: str,
                 from_address: str, from_zip_code: str, from_city: str,
                 receiver_name: str, receiver_cvr_no: Optional[str], to_address: str, to_zip_code: str, to_city: str,
                 registration_no: int, account_no: int):
        self._template = Template(
            source=TEMPLATE_CONTENT,
        )
        self._template.environment.undefined = StrictUndefined

        self.title = title
        self.invoice_no = invoice_no
        self.invoice_no_prefix = invoice_no_prefix

        self.sender_name = sender_name
        self.sender_cvr_no = sender_cvr_no
        self.sender_email = sender_email

        self.from_address = from_address
        self.from_zip_code = from_zip_code
        self.from_city = from_city

        self.receiver_name = receiver_name
        self.receiver_cvr_no = receiver_cvr_no
        self.to_address = to_address
        self.to_zip_code = to_zip_code
        self.to_city = to_city

        self.registration_no = registration_no
        self.account_no = account_no

    def generate_html(self, pdf_output_file: Path,
                      currency: str, additional_sponsorship: Optional[float], tickets: Dict[str, TicketInfo]):
        dt = datetime.now()
        locale.setlocale(category=locale.LC_ALL, locale=locale.getlocale())

        total_sum = 0.0

        if additional_sponsorship:
            total_sum += additional_sponsorship
            additional_sponsorship = locale.format_string('%.2f', float(additional_sponsorship), grouping=True)
        else:
            additional_sponsorship = None

        orders: List[Order] = []
        for ticket_name, info in tickets.items():
            original_price = info.selling_price * 100 / (100 - info.discount_percent)
            sum_of_tickets = (original_price - info.selling_price) * info.sold_tickets
            total_sum += sum_of_tickets

            orders.append(Order(
                count=info.sold_tickets,
                name=ticket_name,
                price_formatted=locale.format_string('%.2f', sum_of_tickets, grouping=True),
            ))

        twemoji_js_file_path = pdf_output_file.parent.joinpath("twemoji.js")
        twemoji_js_content = TWEMOJI_JS_FILE_PATH.read_text().replace(
            "%%%TWEMOJI_JS_CONTENT%%%", TWEMOJI_JS_FILE_PATH.parent.__str__())
        with open(twemoji_js_file_path, "w") as f:
            f.write(twemoji_js_content)

        html_text = self._template.render(
            date=dt.date().__str__(),
            twemoji_js_file_path=twemoji_js_file_path,

            title=f"Faktura: {self.title}",
            invoice_no='{}{}{}'.format(self.invoice_no_prefix, dt.year, self.invoice_no),
            sender_name=self.sender_name,
            sender_cvr_no=self.sender_cvr_no,
            sender_email=html.escape(self.sender_email),

            from_address=self.from_address,
            from_zip_code=self.from_zip_code,
            from_city=self.from_city,

            receiver_name=self.receiver_name,
            receiver_cvr_no=self.receiver_cvr_no,
            to_address=self.to_address,
            to_zip_code=self.to_zip_code,
            to_city=self.to_city,

            registration_no=self.registration_no,
            account_no=self.account_no,

            currency=currency,
            additional_sponsorship=additional_sponsorship,
            orders=orders,
            total_sum=locale.format_string('%.2f', total_sum, grouping=True),
        )

        with open(pdf_output_file.parent.joinpath(f"{pdf_output_file.stem}.html"), "w") as f:
            f.write(html_text)

        if pdf_output_file.parent.exists() and os.access(pdf_output_file.parent, os.W_OK):
            pid = Popen(['wkhtmltopdf', '--enable-local-file-access', '--encoding', 'UTF-8', '--title', self.title,
                         '-', pdf_output_file.__str__()],
                        stdin=PIPE, stderr=PIPE, stdout=PIPE)
            stdout, stderr = pid.communicate(input=html_text.encode())
            exit_code = pid.wait()

            if exit_code == 0:
                print(f"Created the pdf: {pdf_output_file}")
            else:
                print(f"Failed at creating the pdf: {pdf_output_file}")
                print(f"STDOUT:\n{stdout}\n")
                print(f"STDERR:\n{stderr}")
                exit(1)
        else:
            print(f"The folder there you want to safe the generated invoices doesn't exist or"
                  f" you don't have write access: {pdf_output_file.parent}")
            exit(1)

        return bool(total_sum)
