# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
from erpnext_demo.make_random import add_random_children, get_random, how_many, can_make
from frappe.utils import cstr

def run_sales(current_date):
	if can_make("Opportunity"):
		for i in xrange(how_many("Opportunity")):
			make_opportunity(current_date)

	if can_make("Quotation"):
		for i in xrange(how_many("Quotation")):
			make_quotation(current_date)

	if can_make("Sales Order"):
		for i in xrange(how_many("Sales Order")):
			make_sales_order(current_date)

def make_opportunity(current_date):
	b = frappe.get_doc({
		"creation": current_date,
		"doctype": "Opportunity",
		"enquiry_from": "Customer",
		"customer": get_random("Customer"),
		"enquiry_type": "Sales",
		"transaction_date": current_date,
		"fiscal_year": cstr(current_date.year)
	})

	add_random_children(b, "items", rows=4, randomize = {
		"qty": (1, 5),
		"item_code": ("Item", {"is_sales_item": "Yes", "ifnull(has_variants,0)": "0"})
	}, unique="item_code")

	b.insert()
	frappe.db.commit()

def make_quotation(current_date):
	# get open opportunites
	opportunity = get_random("Opportunity", {"status": "Open"})

	if opportunity:
		from erpnext.crm.doctype.opportunity.opportunity import make_quotation
		qtn = frappe.get_doc(make_quotation(opportunity))
		qtn.insert()
		frappe.db.commit()
		qtn.submit()
		frappe.db.commit()
	else:
		# make new directly
		qtn = frappe.get_doc({
			"creation": current_date,
			"doctype": "Quotation",
			"quotation_to": "Customer",
			"customer": get_random("Customer"),
			"order_type": "Sales",
			"transaction_date": current_date,
			"fiscal_year": cstr(current_date.year)
		})

		add_random_children(qtn, "items", rows=3, randomize = {
			"qty": (1, 5),
			"item_code": ("Item", {"is_sales_item": "Yes", "ifnull(has_variants,0)": "0"})
		}, unique="item_code")

		qtn.insert()
		frappe.db.commit()
		qtn.submit()
		frappe.db.commit()

def make_sales_order(current_date):
	q = get_random("Quotation", {"status": "Submitted"})
	if q:
		from erpnext.selling.doctype.quotation.quotation import make_sales_order
		so = frappe.get_doc(make_sales_order(q))
		so.transaction_date = current_date
		so.delivery_date = frappe.utils.add_days(current_date, 10)
		so.fiscal_year = cstr(current_date.year)
		so.insert()
		frappe.db.commit()
		so.submit()
		frappe.db.commit()
