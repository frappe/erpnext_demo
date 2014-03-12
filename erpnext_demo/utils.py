# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import erpnext_demo.make_demo

def on_login(login_manager):
	from frappe.utils import validate_email_add
	if "demo_notify_url" in frappe.conf:
		if frappe.form_dict.lead_email and validate_email_add(frappe.form_dict.lead_email):
			import requests
			url = frappe.conf.demo_notify_url
			cmd = frappe.conf.demo_notify_cmd or "erpnext.templates.utils.send_message"
			response = requests.post(url, data={
				"cmd": cmd,
				"subject":"Logged into Demo",
				"sender": frappe.form_dict.lead_email,
				"message": "via demo.frappecloud.com"
			})

def get_startup_js():
	return """frappe.ui.toolbar.show_banner('You are using ERPNext Demo. '
		+'To start your own ERPNext Trial, <a href="https://erpnext.com/pricing-and-signup" '
		+'target="_blank">click here</a>');"""

def check_if_not_setup():
	if frappe.db.sql("""select name from tabCompany"""):
		raise Exception("Demo App must only be installed on a blank database!")

def make_demo():
	frappe.flags.mute_emails = 1
	make_demo_user()
	make_demo_login_page()
	erpnext_demo.make_demo.make()

def make_demo_user():
	from frappe.auth import _update_password
	
	roles = ["Accounts Manager", "Analytics", "Expense Approver", "Accounts User", 
		"Leave Approver", "Blogger", "Customer", "Sales Manager", "Employee", "Support Manager", 
		"HR Manager", "HR User", "Maintenance Manager", "Maintenance User", "Material Manager", 
		"Material Master Manager", "Material User", "Manufacturing Manager", 
		"Manufacturing User", "Projects User", "Purchase Manager", "Purchase Master Manager", 
		"Purchase User", "Quality Manager", "Report Manager", "Sales Master Manager", 
		"Sales User", "Supplier", "Support Team"]
		
	def add_roles(bean):
		for role in roles:
			p.doclist.append({
				"doctype": "UserRole",
				"parentfield": "user_roles",
				"role": role
			})
	
	# make demo user
	if frappe.db.exists("User", "demo@erpnext.com"):
		frappe.delete_doc("User", "demo@erpnext.com")

	p = frappe.new_bean("User")
	p.doc.email = "demo@erpnext.com"
	p.doc.first_name = "Demo"
	p.doc.last_name = "User"
	p.doc.enabled = 1
	p.doc.user_type = "ERPNext Demo"
	p.insert()
	add_roles(p)
	p.save()
	_update_password("demo@erpnext.com", "demo")
	
	# only read for newsletter
	frappe.db.sql("""update `tabDocPerm` set `write`=0, `create`=0, `cancel`=0
		where parent='Newsletter'""")
	frappe.db.sql("""update `tabDocPerm` set `write`=0, `create`=0, `cancel`=0
		where parent='User' and role='All'""")
	
	frappe.db.commit()

def make_demo_login_page():
	import frappe.installer
	
	frappe.installer.add_to_installed_apps("erpnext_demo")
	
	website_settings = frappe.bean("Website Settings", "Website Settings")
	website_settings.doc.home_page = "start"
	website_settings.doc.disable_signup = 1
	website_settings.save()
	frappe.db.commit()
