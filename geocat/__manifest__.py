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
        'product',
        'account_payment',
        'sale_subscription',
    ],
    'data': [
        'security/licensing_security.xml',
        'security/ir.model.access.csv',
        'views/licensing_views.xml',
        'views/licensing_menus.xml',
        'views/product_template_views.xml',
        'views/account_payment_term_views.xml',
        'views/sale_order_views.xml',
        'views/subscription_plan_views.xml',
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
        # 'web.assets_frontend': [
        #     'geocat/static/src/webclient/home_menu/home_menu_background.scss',
        # ],
        "web.dark_mode_variables": [
            # web._assets_primary_variables
            ('before', 'geocat/static/src/scss/primary_variables.scss',
             'geocat/static/src/scss/primary_variables.dark.scss'),
        ],
        # "web.assets_web_dark": [
        #     # web._assets_frontend
        #     'geocat/static/src/webclient/home_menu/home_menu_background.dark.scss',
        # ],
    },
    'pre_init_hook': '_pre_init_hook',
    'uninstall_hook': '_uninstall_hook',
    'application': True,
    'installable': True,
    'author': 'GeoCat B.V.',
    'maintainer': 'Sander Schaminée',
    'license': 'Other proprietary'
}
