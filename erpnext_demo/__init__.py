import frappe
import frappe.utils.make_random

frappe.utils.make_random.settings = settings = frappe._dict(
	company = "Wind Power LLC",
	company_abbr = "WP",
	country = "United States",
	currency = "USD",
	time_zone = "America/New_York",
	bank_name = "Citibank",
	prob = {
		"default": { "make": 0.6, "qty": (1,5) },
		"Sales Order": { "make": 0.4, "qty": (1,3) },
		"Purchase Order": { "make": 0.7, "qty": (1,15) },
		"Purchase Receipt": { "make": 0.7, "qty": (1,15) },
		"Project": { "make": 0.05 },
		"Task": { "make": 0.5 },
		"Stock Reconciliation": { "make": 0.05 },
		"Subcontract": { "make": 0.05 }
	}
)
