
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
from frappe.utils.make_random import how_many, can_make
from frappe.utils import random_string
from frappe.desk import query_report
from erpnext_demo import settings


def run_accounts(current_date):
	if can_make("Sales Invoice"):
		from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice
		report = "Ordered Items to be Billed"
		for so in list(set([r[0] for r in query_report.run(report)["result"] if r[0]!="Total"]))[:how_many("Sales Invoice")]:
			si = frappe.get_doc(make_sales_invoice(so))
			si.posting_date = current_date
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
			pi.bill_no = random_string(6)
			pi.insert()
			pi.submit()
			frappe.db.commit()

	from erpnext.accounts.doctype.journal_entry.journal_entry import get_payment_entry_against_invoice

	if can_make("Payment Received"):
		report = "Accounts Receivable"
		for si in list(set([r[3] for r in query_report.run(report, {"report_date": current_date })["result"] if r[2]=="Sales Invoice"]))[:how_many("Payment Received")]:
			jv = frappe.get_doc(get_payment_entry_against_invoice("Sales Invoice", si))
			jv.posting_date = current_date
			jv.cheque_no = random_string(6)
			jv.cheque_date = current_date
			jv.insert()
			jv.submit()
			frappe.db.commit()

	if can_make("Payment Made"):
		report = "Accounts Payable"
		for pi in list(set([r[3] for r in query_report.run(report, {"report_date": current_date })["result"] if r[2]=="Purchase Invoice"]))[:how_many("Payment Made")]:
			jv = frappe.get_doc(get_payment_entry_against_invoice("Purchase Invoice", pi))
			jv.posting_date = current_date
			jv.cheque_no = random_string(6)
			jv.cheque_date = current_date
			jv.insert()
			jv.submit()
			frappe.db.commit()
