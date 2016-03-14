# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
from erpnext_demo import settings
from frappe.utils import random_string

def run_hr(current_date):
	year, month = current_date.strftime("%Y-%m").split("-")

	# process payroll
	if not frappe.db.get_value("Salary Slip", {"month": month, "fiscal_year": year}):
		process_payroll = frappe.get_doc("Process Payroll", "Process Payroll")
		process_payroll.company = settings.company
		process_payroll.month = month
		process_payroll.fiscal_year = year
		process_payroll.create_sal_slip()
		process_payroll.submit_salary_slip()
		r = process_payroll.make_journal_entry("Salary - WP")

		journal_entry = frappe.get_doc(r)
		journal_entry.cheque_no = random_string(10)
		journal_entry.cheque_date = current_date
		journal_entry.insert()
		journal_entry.submit()


