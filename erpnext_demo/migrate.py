import json, frappe
from frappe.frappeclient import FrappeClient

def migrate():
	print "connecting..."
	remote = FrappeClient("https://demo2.frappecloud.com", "Administrator", "Wv0CuyWGwrevPX2T")
	boms = []
	for bom in remote.get_list("BOM", fields=["name"]):
		bom = remote.get_doc("BOM", bom.get("name"))
		boms.append(bom)

	with open(frappe.get_app_path("erpnext_demo", "demo_docs", "BOM.json"), "w") as f:
		f.write(json.dumps(boms, sort_keys=True, indent=1))
