$(document).on("desktop-render", function() {
	if (user === "demo@erpnext.com") {
		frappe.desktop.all_applications.show = function() {
			msgprint(__("This feature is disabled for ERPNext Demo."));
		}
	}
});
