# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
from erpnext_demo import settings
from frappe.utils import random_string

def run_hr(current_date):
	year, month = current_date.strftime("%Y-%m").split("-")

	# process payroll
	if not frappe.db.get_value("Salary Slip", {"month": month, "fiscal_year": year}):
		salary_manager = frappe.get_doc("Salary Manager", "Salary Manager")
		salary_manager.company = settings.company
		salary_manager.month = month
		salary_manager.fiscal_year = year
		salary_manager.create_sal_slip()
		salary_manager.submit_salary_slip()
		r = salary_manager.make_journal_entry("Salary - WP")

		journal_entry = frappe.get_doc(r)
		journal_entry.cheque_no = random_string(10)
		journal_entry.cheque_date = current_date
		journal_entry.insert()
		journal_entry.submit()


