# -*- coding: utf-8 -*-
from . import proxy_fix
from . import controllers
from . import models


def _pre_init_hook(env):
    """
    Adds Bridge license-related columns to the sale.order.line model when the module is installed.
    """
    env.cr.execute("""
        ALTER TABLE "account_payment_term"
        ADD COLUMN IF NOT EXISTS "is_default" bool NOT NULL default FALSE""", log_exceptions=True)
    env.cr.execute("""
        ALTER TABLE "sale_subscription_plan"
        ADD COLUMN IF NOT EXISTS "is_default" bool NOT NULL default FALSE""", log_exceptions=True)


def _uninstall_hook(env):
    """
    Removes Bridge license-related columns from the sale.order.line model when the module is uninstalled.
    """
    # TODO: Evaluate if we really need this - probably better to not delete data once in production
    env.cr.execute("""
        ALTER TABLE "product_template"
        DROP COLUMN IF EXISTS bridge_seats
    """)
    env.cr.execute("""
        DROP TABLE IF EXISTS "geocat_license_keys" CASCADE
    """)
    env.cr.execute("""
        DROP TABLE IF EXISTS "geocat_license_checkouts"
    """)
    env.cr.execute("""
        DROP TABLE IF EXISTS "geocat_license_downloads"
    """)

    # Remove our ProxyFix
    if isinstance(proxy_fix.odoo_http.root, proxy_fix.ProxyFixApplication):
        proxy_fix.odoo_http.root = proxy_fix.odoo_http.root.app
