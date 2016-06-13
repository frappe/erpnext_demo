# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _, throw
import erpnext_demo.make_demo
from frappe.utils.password import update_password

def on_login(login_manager):
	from frappe.utils import validate_email_add
	if "demo_notify_url" in frappe.conf:
		if frappe.form_dict.lead_email and validate_email_add(frappe.form_dict.lead_email):
			import requests
			url = frappe.conf.demo_notify_url
			cmd = frappe.conf.demo_notify_cmd or "erpnext.templates.utils.send_message"
			r = requests.post(url, data={
				"cmd": cmd,
				"subject":"Logged into Demo",
				"sender": frappe.form_dict.lead_email,
				"message": "via demo.erpnext.com"
			})

def check_if_not_setup():
	if frappe.db.sql("""select name from tabCompany"""):
		raise Exception("Demo App must only be installed on a blank database!")

def make_demo():
	frappe.flags.mute_emails = 1
	make_demo_user()
	make_demo_login_page()
	erpnext_demo.make_demo.make()

def make_demo_user():
	roles = ["Accounts Manager", "Analytics", "Expense Approver", "Accounts User",
		"Leave Approver", "Blogger", "Customer", "Sales Manager", "Employee",
		"HR Manager", "HR User", "Maintenance Manager", "Maintenance User", "Stock Manager",
		"Item Manager", "Stock User", "Manufacturing Manager",
		"Manufacturing User", "Projects User", "Purchase Manager", "Purchase Master Manager",
		"Purchase User", "Quality Manager", "Report Manager", "Sales Master Manager",
		"Sales User", "Supplier", "Support Team", "Newsletter Manager"]

	def add_roles(doc):
		for role in roles:
			if not frappe.db.exists("Role", role):
				role_doc = frappe.get_doc({
					"doctype": "Role",
					"role_name": role
				})
				role_doc.save()

			doc.append("user_roles", {
				"doctype": "UserRole",
				"role": role
			})

	# make demo user
	if frappe.db.exists("User", "demo@erpnext.com"):
		frappe.delete_doc("User", "demo@erpnext.com")

	# add User Type property setter
	user_types = frappe.get_meta("User").get_field("user_type").options
	frappe.make_property_setter({
		"doctype_or_field": "DocField",
		"doctype": "User",
		"fieldname": "user_type",
		"property": "options",
		"value": (user_types or "") + "\nERPNext Demo",
		"property_type": "Text"
	})

	p = frappe.new_doc("User")
	p.email = "demo@erpnext.com"
	p.first_name = "Demo"
	p.last_name = "User"
	p.enabled = 1
	p.user_type = "ERPNext Demo"
	p.insert()
	add_roles(p)
	p.save()
	update_password("demo@erpnext.com", "demo")

	# only read for newsletter
	frappe.db.sql("""update `tabDocPerm` set `write`=0, `create`=0, `cancel`=0
		where parent='Newsletter'""")
	frappe.db.sql("""update `tabDocPerm` set `write`=0, `create`=0, `cancel`=0
		where parent='User' and role='All'""")

	frappe.db.commit()

def make_demo_login_page():
	import frappe.installer

	frappe.installer.add_to_installed_apps("erpnext_demo")

	website_settings = frappe.get_doc("Website Settings", "Website Settings")
	website_settings.home_page = "start"
	website_settings.disable_signup = 1
	website_settings.save()
	frappe.db.commit()

def validate_reset_password(doc, method):
	if doc.name == "demo@erpnext.com":
		throw(_("You cannot reset the password of {0}").format(doc.first_name + " " + doc.last_name))
