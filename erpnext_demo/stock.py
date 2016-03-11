# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe, random
from frappe.utils.make_random import how_many, can_make
from frappe.utils import cstr
from frappe.desk import query_report
from erpnext_demo import settings
from erpnext.stock.stock_ledger import NegativeStockError
from erpnext.stock.doctype.serial_no.serial_no import SerialNoRequiredError, SerialNoQtyError

def run_stock(current_date):
	make_purchase_receipt(current_date)
	make_delivery_note(current_date)
	make_stock_reconciliation(current_date)
	submit_draft_stock_entries(current_date)

def make_purchase_receipt(current_date):
	if can_make("Purchase Receipt"):
		from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt
		report = "Purchase Order Items To Be Received"
		po_list =list(set([r[0] for r in query_report.run(report)["result"] if r[0]!="'Total'"]))[:how_many("Purchase Receipt")]
		for po in po_list:
			pr = frappe.get_doc(make_purchase_receipt(po))

			if pr.is_subcontracted=="Yes":
				pr.supplier_warehouse = "Supplier - WP"

			pr.posting_date = current_date
			pr.insert()
			try:
				pr.submit()
				frappe.db.commit()
			except (NegativeStockError, SerialNoRequiredError, SerialNoQtyError):
				frappe.db.rollback()

def make_delivery_note(current_date):
	# make purchase requests

	# make delivery notes (if possible)
	if can_make("Delivery Note"):
		from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note
		report = "Ordered Items To Be Delivered"
		for so in list(set([r[0] for r in query_report.run(report)["result"] if r[0]!="'Total'"]))[:how_many("Delivery Note")]:
			dn = frappe.get_doc(make_delivery_note(so))
			dn.posting_date = current_date
			for d in dn.get("items"):
				if not d.expense_account:
					d.expense_account = "Cost of Goods Sold - {}".format(settings.company_abbr)
			dn.insert()
			try:
				dn.submit()
				frappe.db.commit()
			except (NegativeStockError, SerialNoRequiredError, SerialNoQtyError):
				frappe.db.rollback()

def make_stock_reconciliation(current_date):
	# random set some items as damaged
	from erpnext.stock.doctype.stock_reconciliation.stock_reconciliation \
		import OpeningEntryAccountError, EmptyStockReconciliationItemsError

	if can_make("Stock Reconciliation"):
		stock_reco = frappe.new_doc("Stock Reconciliation")
		stock_reco.posting_date = current_date
		stock_reco.get_items_for("Stores - WP")
		if stock_reco.items:
			for item in stock_reco.items:
				if item.qty:
					item.qty = item.qty - round(random.random())
			try:
				stock_reco.insert()
				stock_reco.submit()
				frappe.db.commit()
			except OpeningEntryAccountError:
				frappe.db.rollback()
			except EmptyStockReconciliationItemsError:
				frappe.db.rollback()

def submit_draft_stock_entries(current_date):
	from erpnext.stock.doctype.stock_entry.stock_entry import IncorrectValuationRateError, \
		DuplicateEntryForProductionOrderError, OperationsNotCompleteError

	# try posting older drafts (if exists)
	for st in frappe.db.get_values("Stock Entry", {"docstatus":0}, "name"):
		try:
			ste = frappe.get_doc("Stock Entry", st[0])
			ste.posting_date = current_date
			ste.save()
			ste.submit()
			frappe.db.commit()
		except (NegativeStockError, IncorrectValuationRateError, DuplicateEntryForProductionOrderError,
			OperationsNotCompleteError):
			frappe.db.rollback()

