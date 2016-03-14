# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import sys
import frappe
import random
from frappe.utils.make_random import get_random, can_make
from erpnext_demo.selling import run_sales
from erpnext_demo.accounts import run_accounts
from erpnext_demo.stock import run_stock
from erpnext_demo.buying import run_purchase
from erpnext_demo.manufacturing import run_manufacturing
from erpnext_demo.projects import run_projects
from erpnext_demo.hr import run_hr

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

		run_hr(current_date)
		run_sales(current_date)
		run_purchase(current_date)
		run_manufacturing(current_date)
		run_stock(current_date)
		run_accounts(current_date)
		run_projects(current_date)
		run_messages(current_date)

		current_date = frappe.utils.add_days(current_date, 1)

def run_messages(current_date):
	if can_make("Message"):
		make_message(current_date)

def make_message(current_date):
	from_user = ["demo@erpnext.com", "Administrator"][random.randint(0, 1)]
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

	d = frappe.new_doc('Communication')
	d.communication_type = 'Chat'
	d.user = from_user
	d.owner = from_user
	d.reference_name = to_user
	d.reference_doctype = 'User'
	d.content = comments[random.randint(0, len(comments) - 1)]
	d.insert(ignore_permissions=True)


