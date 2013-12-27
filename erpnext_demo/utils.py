# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import webnotes
import erpnext_demo.make_demo

def on_login(login_manager):
	from webnotes.utils import validate_email_add
	if "demo_notify_url" in webnotes.conf:
		if webnotes.form_dict.lead_email and validate_email_add(webnotes.form_dict.lead_email):
			import requests
			response = requests.post(webnotes.conf.demo_notify_url, data={
				"cmd":"erpnext.templates.utils.send_message",
				"subject":"Logged into Demo",
				"sender": webnotes.form_dict.lead_email,
				"message": "via demo.erpnext.com"
			})

def get_startup_js():
	return """wn.ui.toolbar.show_banner('You are using ERPNext Demo. '
		+'To start your own ERPNext Trial, <a href="https://erpnext.com/pricing-and-signup" '
		+'target="_blank">click here</a>');"""

def check_if_not_setup():
	if webnotes.conn.sql("""select name from tabCompany"""):
		raise Exception("Demo App must only be installed on a blank database!")

def make_demo():
	webnotes.flags.mute_emails = 1
	make_demo_user()
	make_demo_login_page()
	erpnext_demo.make_demo.make()

def make_demo_user():
	from webnotes.auth import _update_password
	
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
	if webnotes.conn.exists("Profile", "demo@erpnext.com"):
		webnotes.delete_doc("Profile", "demo@erpnext.com")

	p = webnotes.new_bean("Profile")
	p.doc.email = "demo@erpnext.com"
	p.doc.first_name = "Demo"
	p.doc.last_name = "User"
	p.doc.enabled = 1
	p.doc.user_type = "ERPNext Demo"
	p.insert()
	add_roles(p)
	p.save()
	_update_password("demo@erpnext.com", "demo")
	
	# make system manager user
	if webnotes.conn.exists("Profile", "admin@erpnext.com"):
		webnotes.delete_doc("Profile", "admin@erpnext.com")
	
	p = webnotes.new_bean("Profile")
	p.doc.email = "admin@erpnext.com"
	p.doc.first_name = "Admin"
	p.doc.last_name = "User"
	p.doc.enabled = 1
	p.doc.user_type = "System User"
	p.insert()
	roles.append("System Manager")
	add_roles(p)
	p.save()
	_update_password("admin@erpnext.com", "admin010123")
	
	# only read for newsletter
	webnotes.conn.sql("""update `tabDocPerm` set `write`=0, `create`=0, `cancel`=0
		where parent='Newsletter'""")
	webnotes.conn.sql("""update `tabDocPerm` set `write`=0, `create`=0, `cancel`=0
		where parent='Profile' and role='All'""")
	
	webnotes.conn.commit()

def make_demo_login_page():
	import webnotes.installer
	
	webnotes.installer.add_to_installed_apps("erpnext_demo")
	
	website_settings = webnotes.bean("Website Settings", "Website Settings")
	website_settings.doc.home_page = "start"
	website_settings.doc.disable_signup = 1
	website_settings.save()
	webnotes.conn.commit()
