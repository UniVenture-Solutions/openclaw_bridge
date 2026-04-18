app_name = "openclaw_bridge"
app_title = "OpenClaw Bridge"
app_publisher = "Unitrade"
app_description = "Readonly analytics bridge for OpenClaw via MCP"
app_email = "admin@nasirkhan.org"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "openclaw_bridge",
# 		"logo": "/assets/openclaw_bridge/logo.png",
# 		"title": "OpenClaw Bridge",
# 		"route": "/openclaw_bridge",
# 		"has_permission": "openclaw_bridge.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/openclaw_bridge/css/openclaw_bridge.css"
# app_include_js = "/assets/openclaw_bridge/js/openclaw_bridge.js"

# include js, css files in header of web template
# web_include_css = "/assets/openclaw_bridge/css/openclaw_bridge.css"
# web_include_js = "/assets/openclaw_bridge/js/openclaw_bridge.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "openclaw_bridge/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "openclaw_bridge/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "openclaw_bridge.utils.jinja_methods",
# 	"filters": "openclaw_bridge.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "openclaw_bridge.install.before_install"
after_install = "openclaw_bridge.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "openclaw_bridge.uninstall.before_uninstall"
# after_uninstall = "openclaw_bridge.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "openclaw_bridge.utils.before_app_install"
# after_app_install = "openclaw_bridge.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "openclaw_bridge.utils.before_app_uninstall"
# after_app_uninstall = "openclaw_bridge.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "openclaw_bridge.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"openclaw_bridge.tasks.all"
# 	],
# 	"daily": [
# 		"openclaw_bridge.tasks.daily"
# 	],
# 	"hourly": [
# 		"openclaw_bridge.tasks.hourly"
# 	],
# 	"weekly": [
# 		"openclaw_bridge.tasks.weekly"
# 	],
# 	"monthly": [
# 		"openclaw_bridge.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "openclaw_bridge.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "openclaw_bridge.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "openclaw_bridge.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "openclaw_bridge.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["openclaw_bridge.utils.before_request"]
# after_request = ["openclaw_bridge.utils.after_request"]

# Job Events
# ----------
# before_job = ["openclaw_bridge.utils.before_job"]
# after_job = ["openclaw_bridge.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"openclaw_bridge.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []
