# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
from erpnext_demo.make_random import how_many, can_make
from frappe.utils import cstr
from frappe.desk import query_report
from erpnext_demo import settings

def run_stock(current_date):
	# make purchase requests
	from erpnext.stock.stock_ledger import NegativeStockError

	if can_make("Purchase Receipt"):
		from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt
		report = "Purchase Order Items To Be Received"
		po_list =list(set([r[0] for r in query_report.run(report)["result"] if r[0]!="Total"]))[:how_many("Purchase Receipt")]
		for po in po_list:
			pr = frappe.get_doc(make_purchase_receipt(po))
			pr.posting_date = current_date
			pr.fiscal_year = cstr(current_date.year)
			pr.insert()
			pr.submit()
			frappe.db.commit()

	# make delivery notes (if possible)
	if can_make("Delivery Note"):
		from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note
		from erpnext.stock.doctype.serial_no.serial_no import SerialNoRequiredError, SerialNoQtyError
		report = "Ordered Items To Be Delivered"
		for so in list(set([r[0] for r in query_report.run(report)["result"] if r[0]!="Total"]))[:how_many("Delivery Note")]:
			dn = frappe.get_doc(make_delivery_note(so))
			dn.posting_date = current_date
			dn.fiscal_year = cstr(current_date.year)
			for d in dn.get("items"):
				if not d.expense_account:
					d.expense_account = "Cost of Goods Sold - {}".format(settings.company_abbr)

			dn.insert()
			try:
				dn.submit()
				frappe.db.commit()
			except (NegativeStockError, SerialNoRequiredError, SerialNoQtyError):
				frappe.db.rollback()
