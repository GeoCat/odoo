# -*- coding: utf-8 -*-

# noinspection PyStatementEffect
{
    'name': 'GeoCat Customizations',
    'category': 'Customizations/GeoCat',
    'version': '0.1',
    'sequence': 151,
    'summary': 'Manage and check out subscription-based (desktop) software licenses',
    'description': """GeoCat Customizations
    
    This module allows internal users to issue and manage software licenses 
    for desktop applications (e.g. GeoCat Bridge).
    Whenever a GeoCat Bridge subscription is sold, a license is automatically created.
    The customer can see the license key in the portal and generate a license file.
    GeoCat employees can suspend, revoke or (re-)issue licenses.
    
    This module also overrides some Odoo models and behaviors, and tweaks the UI/UX for GeoCat internal purposes.
    """,
    'depends': [
        'base',
        'portal',
        # 'website',
        'product',
        'account',
        'sale_subscription',
    ],
    'data': [
        'security/licensing_security.xml',
        'security/ir.model.access.csv',
        'views/licensing_checkout_views.xml',
        'views/licensing_download_views.xml',
        'views/licensing_views.xml',
        'views/licensing_menus.xml',
        'views/product_template_views.xml',
        'views/account_payment_term_views.xml',
        'views/sale_order_views.xml',
        'views/subscription_plan_views.xml',
        'views/report_templates.xml',
        'views/portal_templates.xml',
        'views/webclient_templates.xml',
        'report/sale_order_templates.xml',
        'report/invoice_templates.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            ('before', 'web_enterprise/static/src/scss/primary_variables.scss',
             'geocat/static/src/scss/primary_variables.scss'),
        ],
        'web._assets_backend_helpers': [
            ('before', 'web_enterprise/static/src/scss/bootstrap_overridden.scss',
             'geocat/static/src/scss/bootstrap_overridden.scss'),
        ],
        'web.assets_frontend': [
            ('replace', 'web_enterprise/static/src/webclient/home_menu/home_menu_background.scss',
             'geocat/static/src/webclient/home_menu/home_menu_background.scss'),
        ],
        'web.assets_backend': [
            ('after', 'web/static/src/views/view.scss', 'geocat/static/src/views/view.scss'),
            ('replace', 'web_enterprise/static/src/webclient/home_menu/home_menu_background.scss',
             'geocat/static/src/webclient/home_menu/home_menu_background.scss'),
            ('after', 'web_editor/static/src/scss/web_editor.common.scss',
             'geocat/static/src/scss/web_editor.common.scss'),
        ],
        'web.dark_mode_variables': [
            # Dark mode override for web._assets_primary_variables
            ('before', 'geocat/static/src/scss/primary_variables.scss',
             'geocat/static/src/scss/primary_variables.dark.scss'),
        ],
        'web.assets_web_dark': [
            # Dark mode override for web._assets_frontend, web._assets_backend
            ('replace', 'web_enterprise/static/src/webclient/home_menu/home_menu_background.dark.scss',
             'geocat/static/src/webclient/home_menu/home_menu_background.dark.scss'),
            ('after', 'web/static/src/webclient/webclient.scss', 'geocat/static/src/webclient/webclient.dark.scss'),
        ],
        'web.report_assets_common': [
            ('after', 'web/static/fonts/fonts.scss', '/geocat/static/fonts/geocat_fonts.scss'),
            ('after', 'web/static/src/webclient/actions/reports/report.scss',
             '/geocat/static/src/webclient/actions/reports/report.scss'),
        ],
    },
    'pre_init_hook': '_pre_init_hook',
    'uninstall_hook': '_uninstall_hook',
    'application': True,
    'installable': True,
    'author': 'GeoCat B.V.',
    'maintainer': 'Sander Schaminée',
    'license': 'Other proprietary'
}
