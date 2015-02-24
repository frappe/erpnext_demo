
# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
from erpnext_demo.make_random import how_many, can_make
from frappe.utils import cstr, random_string
from frappe.desk import query_report
from erpnext_demo import settings


def run_accounts(current_date):
	if can_make("Sales Invoice"):
		from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice
		report = "Ordered Items to be Billed"
		for so in list(set([r[0] for r in query_report.run(report)["result"] if r[0]!="Total"]))[:how_many("Sales Invoice")]:
			si = frappe.get_doc(make_sales_invoice(so))
			si.posting_date = current_date
			si.fiscal_year = cstr(current_date.year)
			for d in si.get("items"):
				if not d.income_account:
					d.income_account = "Sales - {}".format(settings.company_abbr)
			si.insert()
			si.submit()
			frappe.db.commit()

	if can_make("Purchase Invoice"):
		from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_invoice
		report = "Received Items to be Billed"
		for pr in list(set([r[0] for r in query_report.run(report)["result"] if r[0]!="Total"]))[:how_many("Purchase Invoice")]:
			pi = frappe.get_doc(make_purchase_invoice(pr))
			pi.posting_date = current_date
			pi.fiscal_year = cstr(current_date.year)
			pi.bill_no = random_string(6)
			pi.insert()
			pi.submit()
			frappe.db.commit()

	if can_make("Payment Received"):
		from erpnext.accounts.doctype.journal_entry.journal_entry import get_payment_entry_from_sales_invoice
		report = "Accounts Receivable"
		for si in list(set([r[3] for r in query_report.run(report, {"report_date": current_date })["result"] if r[2]=="Sales Invoice"]))[:how_many("Payment Received")]:
			jv = frappe.get_doc(get_payment_entry_from_sales_invoice(si))
			jv.posting_date = current_date
			jv.cheque_no = random_string(6)
			jv.cheque_date = current_date
			jv.insert()
			jv.submit()
			frappe.db.commit()

	if can_make("Payment Made"):
		from erpnext.accounts.doctype.journal_entry.journal_entry import get_payment_entry_from_purchase_invoice
		report = "Accounts Payable"
		for pi in list(set([r[3] for r in query_report.run(report, {"report_date": current_date })["result"] if r[2]=="Purchase Invoice"]))[:how_many("Payment Made")]:
			jv = frappe.get_doc(get_payment_entry_from_purchase_invoice(pi))
			jv.posting_date = current_date
			jv.cheque_no = random_string(6)
			jv.cheque_date = current_date
			jv.insert()
			jv.submit()
			frappe.db.commit()
