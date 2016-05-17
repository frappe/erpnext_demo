# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
from frappe.utils.make_random import add_random_children, get_random, how_many, can_make
from frappe.utils import cstr
from erpnext.setup.utils import get_exchange_rate
from erpnext.accounts.party import get_party_account_currency

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
	})

	add_random_children(b, "items", rows=4, randomize = {
		"qty": (1, 5),
		"item_code": ("Item", {"has_variants": "0"})
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

		# get customer, currency and exchange_rate
		customer = get_random("Customer")

		company_currency = frappe.db.get_value("Company", "Wind Power LLC", "default_currency")
		party_account_currency = get_party_account_currency("Customer", customer, "Wind Power LLC")
		if company_currency == party_account_currency:
			exchange_rate = 1
		else:
			exchange_rate = get_exchange_rate(party_account_currency, company_currency)

		qtn = frappe.get_doc({
			"creation": current_date,
			"doctype": "Quotation",
			"quotation_to": "Customer",
			"customer": customer,
			"currency": party_account_currency or company_currency,
			"conversion_rate": exchange_rate,
			"order_type": "Sales",
			"transaction_date": current_date,
		})

		add_random_children(qtn, "items", rows=3, randomize = {
			"qty": (1, 5),
			"item_code": ("Item", {"has_variants": "0"})
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
		so.insert()
		frappe.db.commit()
		so.submit()
		frappe.db.commit()
