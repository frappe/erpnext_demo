# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe, os, datetime
import frappe.utils
from frappe.utils import random_string, cstr
from frappe.widgets import query_report
import random
import json

from frappe.core.page.data_import_tool.data_import_tool import import_doc
# fix price list
# fix fiscal year

company = "Wind Power LLC"
company_abbr = "WP"
country = "United States"
currency = "USD"
time_zone = "America/New_York"
start_date = None
runs_for = None
bank_name = "Citibank"
prob = {
	"default": { "make": 0.6, "qty": (1,5) },
	"Sales Order": { "make": 0.4, "qty": (1,3) },
	"Purchase Order": { "make": 0.7, "qty": (1,15) },
	"Purchase Receipt": { "make": 0.7, "qty": (1,15) },
}

def make():
	#frappe.flags.print_messages = True
	frappe.flags.mute_emails = True
	frappe.flags.rollback_on_exception = True
	setup()
	_simulate()

def setup():
	complete_setup()
	make_customers_suppliers_contacts()
	show_item_groups_in_website()
	make_items()
	make_price_lists()
	make_users_and_employees()
	make_bank_account()
	# make_opening_stock()
	# make_opening_accounts()

	make_tax_accounts()
	make_tax_masters()
	make_shipping_rules()
	if "shopping_cart" in frappe.get_installed_apps():
		enable_shopping_cart()

def _simulate():
	global runs_for, start_date

	if not start_date:
		# start date = 100 days back
		start_date = frappe.utils.add_days(frappe.utils.nowdate(), -1 * (runs_for or 100))

	current_date = frappe.utils.getdate(start_date)

	# continue?
	last_posting = frappe.db.sql("""select max(posting_date) from `tabStock Ledger Entry`""")
	if last_posting[0][0]:
		current_date = frappe.utils.add_days(last_posting[0][0], 1)

	# run till today
	if not runs_for:
		runs_for = frappe.utils.date_diff(frappe.utils.nowdate(), current_date)
		# runs_for = 100

	for i in xrange(runs_for):
		print current_date.strftime("%Y-%m-%d")
		frappe.local.current_date = current_date

		if current_date.weekday() in (5, 6):
			current_date = frappe.utils.add_days(current_date, 1)
			continue

		run_sales(current_date)
		run_purchase(current_date)
		run_manufacturing(current_date)
		run_stock(current_date)
		run_accounts(current_date)

		current_date = frappe.utils.add_days(current_date, 1)

def run_sales(current_date):
	if can_make("Quotation"):
		for i in xrange(how_many("Quotation")):
			make_quotation(current_date)

	if can_make("Sales Order"):
		for i in xrange(how_many("Sales Order")):
			make_sales_order(current_date)

def run_accounts(current_date):
	if can_make("Sales Invoice"):
		from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice
		report = "Ordered Items to be Billed"
		for so in list(set([r[0] for r in query_report.run(report)["result"] if r[0]!="Total"]))[:how_many("Sales Invoice")]:
			si = frappe.get_doc(make_sales_invoice(so))
			si.posting_date = current_date
			si.fiscal_year = cstr(current_date.year)
			for d in si.get("entries"):
				if not d.income_account:
					d.income_account = "Sales - {}".format(company_abbr)
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
		from erpnext.accounts.doctype.journal_voucher.journal_voucher import get_payment_entry_from_sales_invoice
		report = "Accounts Receivable"
		for si in list(set([r[4] for r in query_report.run(report, {"report_date": current_date })["result"] if r[3]=="Sales Invoice"]))[:how_many("Payment Received")]:
			jv = frappe.get_doc(get_payment_entry_from_sales_invoice(si))
			jv.posting_date = current_date
			jv.cheque_no = random_string(6)
			jv.cheque_date = current_date
			jv.fiscal_year = cstr(current_date.year)
			jv.insert()
			jv.submit()
			frappe.db.commit()

	if can_make("Payment Made"):
		from erpnext.accounts.doctype.journal_voucher.journal_voucher import get_payment_entry_from_purchase_invoice
		report = "Accounts Payable"
		for pi in list(set([r[4] for r in query_report.run(report, {"report_date": current_date })["result"] if r[3]=="Purchase Invoice"]))[:how_many("Payment Made")]:
			jv = frappe.get_doc(get_payment_entry_from_purchase_invoice(pi))
			jv.posting_date = current_date
			jv.cheque_no = random_string(6)
			jv.cheque_date = current_date
			jv.fiscal_year = cstr(current_date.year)
			jv.insert()
			jv.submit()
			frappe.db.commit()

def run_stock(current_date):
	# make purchase requests
	if can_make("Purchase Receipt"):
		from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt
		from erpnext.stock.stock_ledger import NegativeStockError
		report = "Purchase Order Items To Be Received"
		for po in list(set([r[0] for r in query_report.run(report)["result"] if r[0]!="Total"]))[:how_many("Purchase Receipt")]:
			pr = frappe.get_doc(make_purchase_receipt(po))
			pr.posting_date = current_date
			pr.fiscal_year = cstr(current_date.year)
			pr.insert()
			try:
				pr.submit()
				frappe.db.commit()
			except NegativeStockError: pass

	# make delivery notes (if possible)
	if can_make("Delivery Note"):
		from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note
		from erpnext.stock.stock_ledger import NegativeStockError
		from erpnext.stock.doctype.serial_no.serial_no import SerialNoRequiredError, SerialNoQtyError
		report = "Ordered Items To Be Delivered"
		for so in list(set([r[0] for r in query_report.run(report)["result"] if r[0]!="Total"]))[:how_many("Delivery Note")]:
			dn = frappe.get_doc(make_delivery_note(so))
			dn.posting_date = current_date
			dn.fiscal_year = cstr(current_date.year)
			for d in dn.get("delivery_note_details"):
				if not d.expense_account:
					d.expense_account = "Cost of Goods Sold - {}".format(company_abbr)

			dn.insert()
			try:
				dn.submit()
				frappe.db.commit()
			except NegativeStockError: pass
			except SerialNoRequiredError: pass
			except SerialNoQtyError: pass

	# try submitting existing
	for dn in frappe.db.get_values("Delivery Note", {"docstatus": 0}, "name"):
		b = frappe.get_doc("Delivery Note", dn[0])
		b.submit()
		frappe.db.commit()

def run_purchase(current_date):
	# make material requests for purchase items that have negative projected qtys
	if can_make("Material Request"):
		report = "Items To Be Requested"
		for row in query_report.run(report)["result"][:how_many("Material Request")]:
			mr = frappe.new_doc("Material Request")
			mr.material_request_type = "Purchase"
			mr.transaction_date = current_date
			mr.fiscal_year = cstr(current_date.year)
			mr.append("indent_details", {
				"doctype": "Material Request Item",
				"schedule_date": frappe.utils.add_days(current_date, 7),
				"item_code": row[0],
				"qty": -row[-1]
			})
			mr.insert()
			mr.submit()

	# make supplier quotations
	if can_make("Supplier Quotation"):
		from erpnext.stock.doctype.material_request.material_request import make_supplier_quotation
		report = "Material Requests for which Supplier Quotations are not created"
		for row in query_report.run(report)["result"][:how_many("Supplier Quotation")]:
			if row[0] != "Total":
				sq = frappe.get_doc(make_supplier_quotation(row[0]))
				sq.transaction_date = current_date
				sq.fiscal_year = cstr(current_date.year)
				sq.insert()
				sq.submit()
				frappe.db.commit()

	# make purchase orders
	if can_make("Purchase Order"):
		from erpnext.stock.doctype.material_request.material_request import make_purchase_order
		report = "Requested Items To Be Ordered"
		for row in query_report.run(report)["result"][:how_many("Purchase Order")]:
			if row[0] != "Total":
				po = frappe.get_doc(make_purchase_order(row[0]))
				po.transaction_date = current_date
				po.fiscal_year = cstr(current_date.year)
				po.insert()
				po.submit()
				frappe.db.commit()

def run_manufacturing(current_date):
	from erpnext.stock.stock_ledger import NegativeStockError
	from erpnext.stock.doctype.stock_entry.stock_entry import IncorrectValuationRateError, DuplicateEntryForProductionOrderError

	ppt = frappe.get_doc("Production Planning Tool", "Production Planning Tool")
	ppt.company = company
	ppt.use_multi_level_bom = 1
	ppt.purchase_request_for_warehouse = "Stores - {}".format(company_abbr)
	ppt.run_method("get_open_sales_orders")
	ppt.run_method("get_items_from_so")
	ppt.run_method("raise_production_order")
	ppt.run_method("raise_purchase_request")
	frappe.db.commit()

	# submit production orders
	for pro in frappe.db.get_values("Production Order", {"docstatus": 0}, "name"):
		b = frappe.get_doc("Production Order", pro[0])
		b.wip_warehouse = "Work in Progress - WP"
		b.submit()
		frappe.db.commit()

	# submit material requests
	for pro in frappe.db.get_values("Material Request", {"docstatus": 0}, "name"):
		b = frappe.get_doc("Material Request", pro[0])
		b.submit()
		frappe.db.commit()

	# stores -> wip
	if can_make("Stock Entry for WIP"):
		for pro in query_report.run("Open Production Orders")["result"][:how_many("Stock Entry for WIP")]:
			make_stock_entry_from_pro(pro[0], "Material Transfer", current_date)

	# wip -> fg
	if can_make("Stock Entry for FG"):
		for pro in query_report.run("Production Orders in Progress")["result"][:how_many("Stock Entry for FG")]:
			make_stock_entry_from_pro(pro[0], "Manufacture/Repack", current_date)

	# try posting older drafts (if exists)
	for st in frappe.db.get_values("Stock Entry", {"docstatus":0}, "name"):
		try:
			frappe.get_doc("Stock Entry", st[0]).submit()
			frappe.db.commit()
		except NegativeStockError: pass
		except IncorrectValuationRateError: pass
		except DuplicateEntryForProductionOrderError: pass

def make_stock_entry_from_pro(pro_id, purpose, current_date):
	from erpnext.manufacturing.doctype.production_order.production_order import make_stock_entry
	from erpnext.stock.stock_ledger import NegativeStockError
	from erpnext.stock.doctype.stock_entry.stock_entry import IncorrectValuationRateError, DuplicateEntryForProductionOrderError

	try:
		st = frappe.get_doc(make_stock_entry(pro_id, purpose))
		st.posting_date = current_date
		st.fiscal_year = cstr(current_date.year)
		for d in st.get("mtn_details"):
			d.expense_account = "Stock Adjustment - " + company_abbr
			d.cost_center = "Main - " + company_abbr
		st.insert()
		frappe.db.commit()
		st.submit()
		frappe.db.commit()
	except NegativeStockError: pass
	except IncorrectValuationRateError: pass
	except DuplicateEntryForProductionOrderError: pass

def make_quotation(current_date):
	b = frappe.get_doc({
		"creation": current_date,
		"doctype": "Quotation",
		"quotation_to": "Customer",
		"customer": get_random("Customer"),
		"order_type": "Sales",
		"transaction_date": current_date,
		"fiscal_year": cstr(current_date.year)
	})

	add_random_children(b, {
		"doctype": "Quotation Item",
		"parentfield": "quotation_details",
	}, rows=3, randomize = {
		"qty": (1, 5),
		"item_code": ("Item", {"is_sales_item": "Yes"})
	}, unique="item_code")

	b.insert()
	frappe.db.commit()
	b.submit()
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

def add_random_children(doc, template, rows, randomize, unique=None):
	for i in xrange(random.randrange(1, rows)):
		d = template.copy()
		for key, val in randomize.items():
			if isinstance(val[0], basestring):
				d[key] = get_random(*val)
			else:
				d[key] = random.randrange(*val)

		if unique:
			if not doc.get(d["parentfield"], {unique:d[unique]}):
				doc.append(d["parentfield"], d)
		else:
			doc.append(d["parentfield"], d)

def get_random(doctype, filters=None):
	condition = []
	if filters:
		for key, val in filters.items():
			condition.append("%s='%s'" % (key, val.replace("'", "\'")))
	if condition:
		condition = " where " + " and ".join(condition)
	else:
		condition = ""

	out = frappe.db.sql("""select name from `tab%s` %s
		order by RAND() limit 0,1""" % (doctype, condition))

	return out and out[0][0] or None

def can_make(doctype):
	return random.random() < prob.get(doctype, prob["default"])["make"]

def how_many(doctype):
	return random.randrange(*prob.get(doctype, prob["default"])["qty"])

def install():
	print "Creating Fresh Database..."
	from frappe.install_lib.install import Installer
	from frappe import conf
	inst = Installer('root')
	inst.install(conf.demo_db_name, verbose=1, force=1)

def complete_setup():
	print "Complete Setup..."
	from erpnext.setup.page.setup_wizard.setup_wizard import setup_account
	setup_account({
		"first_name": "Test",
		"last_name": "User",
		"fy_start_date": "2014-01-01",
		"fy_end_date": "2014-12-31",
		"industry": "Manufacturing",
		"company_name": company,
		"company_abbr": company_abbr,
		"currency": currency,
		"timezone": time_zone,
		"country": country
	})

	import_data("Fiscal_Year")

def show_item_groups_in_website():
	"""set show_in_website=1 for Item Groups"""
	for name in frappe.db.sql_list("""select name from `tabItem Group` order by lft"""):
		item_group = frappe.get_doc("Item Group", name)
		item_group.show_in_website = 1
		item_group.save()

def make_items():
	import_data("Item")
	import_data("BOM", submit=True)

def make_price_lists():
	import_data("Item_Price", overwrite=True)

def make_customers_suppliers_contacts():
	import_data(["Customer", "Supplier", "Contact", "Address", "Lead"])

def make_users_and_employees():
	frappe.db.set_value("HR Settings", None, "emp_created_by", "Naming Series")
	frappe.db.commit()

	import_data(["User", "Employee", "Salary_Structure"])

def make_bank_account():
	ba = frappe.get_doc({
		"doctype": "Account",
		"account_name": bank_name,
		"account_type": "Bank",
		"group_or_ledger": "Ledger",
		"parent_account": "Bank Accounts - " + company_abbr,
		"company": company
	}).insert()

	frappe.set_value("Company", company, "default_bank_account", ba.name)
	frappe.db.commit()

def make_tax_accounts():
	import_data("Account")

def make_tax_masters():
	import_data("Sales Taxes and Charges Master")

def make_shipping_rules():
	import_data("Shipping Rule")

def enable_shopping_cart():
	# import
	path = os.path.join(os.path.dirname(__file__), "demo_docs", "Shopping Cart Settings.json")
	import_doc(path)

	# enable
	settings = frappe.get_doc("Shopping Cart Settings")
	settings.enabled = 1
	settings.save()

def import_data(dt, submit=False, overwrite=False):
	if not isinstance(dt, (tuple, list)):
		dt = [dt]

	for doctype in dt:
		print "Importing", doctype.replace("_", " "), "..."
		import_doc(os.path.join(os.path.dirname(__file__), "demo_docs", doctype+".csv"), submit=submit, overwrite=overwrite)

		# doctype = doctype.replace("_", " ").title()
		# print "\n".join(frappe.db.sql_list('select name from `tab{}`'.format(doctype))).encode("utf-8")
		# print
