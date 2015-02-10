$(document).on("desktop-render", function() {
	if (user !== "Administrator") {
		frappe.desktop.all_applications.show = function() {
			msgprint(__("This feature is disabled for ERPNext Demo."));
		}
	}
});
