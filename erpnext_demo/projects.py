# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
from frappe.utils.make_random import can_make

def run_projects(current_date):
	if can_make("Project"):
		make_project(current_date)
		frappe.db.commit()

	if can_make("Task"):
		close_tasks(current_date)
		frappe.db.commit()

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
