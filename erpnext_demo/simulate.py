# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import sys
import frappe
from frappe.utils import random_string, cstr
from frappe.desk import query_report
import random
from erpnext_demo import settings
from erpnext_demo.make_random import add_random_children, get_random, how_many, can_make

start_date = None
runs_for = None

def simulate():
	global runs_for, start_date

	if not start_date:
		# start date = 100 days back
		start_date = frappe.utils.add_days(frappe.utils.nowdate(), -1 * (runs_for or 150))

	current_date = frappe.utils.getdate(start_date)

	# continue?
	last_posting = frappe.db.sql("""select max(posting_date) from `tabStock Ledger Entry` where posting_date < curdate()""")
	if last_posting[0][0]:
		current_date = frappe.utils.add_days(last_posting[0][0], 1)

	# run till today
	if not runs_for:
		runs_for = frappe.utils.date_diff(frappe.utils.nowdate(), current_date)
		# runs_for = 100

	for i in xrange(runs_for):
		sys.stdout.write("\rSimulating {0}".format(current_date.strftime("%Y-%m-%d")))
		sys.stdout.flush()
		frappe.local.current_date = current_date

		if current_date.weekday() in (5, 6):
			current_date = frappe.utils.add_days(current_date, 1)
			continue

		run_sales(current_date)
		run_purchase(current_date)
		run_manufacturing(current_date)
		run_stock(current_date)
		run_accounts(current_date)
		run_projects(current_date)
		run_messages(current_date)

		current_date = frappe.utils.add_days(current_date, 1)

	print ""

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

def run_purchase(current_date):
	# make material requests for purchase items that have negative projected qtys
	if can_make("Material Request"):
		report = "Items To Be Requested"
		for row in query_report.run(report)["result"][:how_many("Material Request")]:
			mr = frappe.new_doc("Material Request")
			mr.material_request_type = "Purchase"
			mr.transaction_date = current_date
			mr.fiscal_year = cstr(current_date.year)
			mr.append("items", {
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
	from erpnext.stock.doctype.stock_entry.stock_entry import IncorrectValuationRateError, DuplicateEntryForProductionOrderError
	from erpnext.stock.stock_ledger import NegativeStockError

	ppt = frappe.get_doc("Production Planning Tool", "Production Planning Tool")
	ppt.company = settings.company
	ppt.use_multi_level_bom = 1
	ppt.purchase_request_for_warehouse = "Stores - {}".format(settings.company_abbr)
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
			make_stock_entry_from_pro(pro[0], "Material Transfer for Manufacture", current_date)

	# wip -> fg
	if can_make("Stock Entry for FG"):
		for pro in query_report.run("Production Orders in Progress")["result"][:how_many("Stock Entry for FG")]:
			make_stock_entry_from_pro(pro[0], "Manufacture", current_date)

	# try posting older drafts (if exists)
	for st in frappe.db.get_values("Stock Entry", {"docstatus":0}, "name"):
		try:
			ste = frappe.get_doc("Stock Entry", st[0])
			ste.posting_date = current_date
			ste.save()
			ste.submit()
			frappe.db.commit()
		except (NegativeStockError, IncorrectValuationRateError, DuplicateEntryForProductionOrderError):
			frappe.db.rollback()

def run_messages(current_date):
	if can_make("Message"):
		make_message(current_date)

def make_message(current_date):
	from_user = ["demo@frappecloud.com", "Administrator"][random.randint(0, 1)]
	to_user = get_random("User")
	comments = [
		"Barnaby The Bear's my name, never call me Jack or James, I will sing my way to fame, Barnaby the Bear's my name.",
		"Birds taught me to sing, when they took me to their king, first I had to fly, in the sky so high so high, so high so high so high, so - if you want to sing this way, think of what you'd like to say, add a tune and you will see, just how easy it can be.",
		"Children of the sun, see your time has just begun, searching for your ways, through adventures every day. ",
		"Every day and night, with the condor in flight, with all your friends in tow, you search for the Cities of Gold.",
		"80 days around the world, we'll find a pot of gold just sitting where the rainbow's ending. ",
		"Time - we'll fight against the time, and we'll fly on the white wings of the wind. ",
		"Knight Rider, a shadowy flight into the dangerous world of a man who does not exist. Michael Knight, a young loner on a crusade to champion the cause of the innocent, the helpless in a world of criminals who operate above the law.",
		"Ulysses, Ulysses - Soaring through all the galaxies. In search of Earth, flying in to the night. Ulysses, Ulysses - Fighting evil and tyranny, with all his power, and with all of his might. Ulysses - no-one else can do the things you do. Ulysses - like a bolt of thunder from the blue. Ulysses - always fighting all the evil forces bringing peace and justice to all.",
		"One for all and all for one, Muskehounds are always ready. One for all and all for one, helping everybody. One for all and all for one, it's a pretty story. "
	]

	d = frappe.new_doc('Comment')
	d.owner = from_user
	d.comment_docname = to_user
	d.comment_doctype = 'Message'
	d.comment = comments[random.randint(0, len(comments) - 1)]
	d.insert(ignore_permissions=True)

def make_stock_entry_from_pro(pro_id, purpose, current_date):
	from erpnext.manufacturing.doctype.production_order.production_order import make_stock_entry
	from erpnext.stock.stock_ledger import NegativeStockError
	from erpnext.stock.doctype.stock_entry.stock_entry import IncorrectValuationRateError, DuplicateEntryForProductionOrderError

	try:
		st = frappe.get_doc(make_stock_entry(pro_id, purpose))
		st.posting_date = current_date
		st.fiscal_year = cstr(current_date.year)
		for d in st.get("items"):
			d.expense_account = "Stock Adjustment - " + settings.company_abbr
			d.cost_center = "Main - " + settings.company_abbr
		st.insert()
		frappe.db.commit()
		st.submit()
		frappe.db.commit()
	except (NegativeStockError, IncorrectValuationRateError, DuplicateEntryForProductionOrderError):
		frappe.db.rollback()

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
		"item_code": ("Item", {"is_sales_item": "Yes", "has_variants": "0"})
	}, unique="item_code")

	b.insert()
	frappe.db.commit()
	b.submit()
	frappe.db.commit()

def make_quotation(current_date):
	# get open opportunites
	opportunity = get_random("Opportunity", {"status": "Submitted"})

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
			"item_code": ("Item", {"is_sales_item": "Yes", "has_variants": "0"})
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

def run_projects(current_date):
	if can_make("Project"):
		make_project(current_date)

	if can_make("Task"):
		close_tasks(current_date)

def close_tasks(current_date):
	for task in frappe.get_all("Task", ["name"], {"status": "Open", "exp_end_date": ("<", current_date)}):
		task = frappe.get_doc("Task", task.name)
		task.status = "Closed"
		task.save()

def make_project(current_date):
	project = frappe.get_doc({
		"doctype": "Project",
		"project_name": "New Product Development " + current_date.strftime("%Y-%m-%d"),
	})
	project.set("tasks", [
			{
				"title": "Review Requirements",
				"start_date": frappe.utils.add_days(current_date, 10),
				"end_date": frappe.utils.add_days(current_date, 11)
			},
			{
				"title": "Design Options",
				"start_date": frappe.utils.add_days(current_date, 11),
				"end_date": frappe.utils.add_days(current_date, 20)
			},
			{
				"title": "Make Prototypes",
				"start_date": frappe.utils.add_days(current_date, 20),
				"end_date": frappe.utils.add_days(current_date, 30)
			},
			{
				"title": "Customer Feedback on Prototypes",
				"start_date": frappe.utils.add_days(current_date, 30),
				"end_date": frappe.utils.add_days(current_date, 40)
			},
			{
				"title": "Freeze Feature Set",
				"start_date": frappe.utils.add_days(current_date, 40),
				"end_date": frappe.utils.add_days(current_date, 45)
			},
			{
				"title": "Testing",
				"start_date": frappe.utils.add_days(current_date, 45),
				"end_date": frappe.utils.add_days(current_date, 60)
			},
			{
				"title": "Product Engineering",
				"start_date": frappe.utils.add_days(current_date, 45),
				"end_date": frappe.utils.add_days(current_date, 55)
			},
			{
				"title": "Supplier Contracts",
				"start_date": frappe.utils.add_days(current_date, 55),
				"end_date": frappe.utils.add_days(current_date, 70)
			},
			{
				"title": "Design and Build Fixtures",
				"start_date": frappe.utils.add_days(current_date, 45),
				"end_date": frappe.utils.add_days(current_date, 65)
			},
			{
				"title": "Test Run",
				"start_date": frappe.utils.add_days(current_date, 70),
				"end_date": frappe.utils.add_days(current_date, 80)
			},
			{
				"title": "Launch",
				"start_date": frappe.utils.add_days(current_date, 80),
				"end_date": frappe.utils.add_days(current_date, 90)
			},
		])
	project.insert()
