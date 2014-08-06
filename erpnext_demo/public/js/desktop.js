$(document).on("desktop-render", function() {
	if (user !== "Administrator") {
		frappe.desktop.show_all_modules = function() {
			msgprint(__("This feature is disabled for ERPNext Demo."));
		}
	}
});
