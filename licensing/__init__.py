# -*- coding: utf-8 -*-

from . import controllers
from . import models


def _pre_init_hook(env):
    """
    Adds Bridge license-related columns to the sale.order.line model when the module is installed.
    """
    env.cr.execute("""
        ALTER TABLE "sale_order_line"
        ADD COLUMN "num_bridge_seats" int4
    """)


def _uninstall_hook(env):
    """
    Removes Bridge license-related columns from the sale.order.line model when the module is uninstalled.
    """
    env.cr.execute("""
        ALTER TABLE "sale_order_line"
        DROP COLUMN "num_bridge_seats"
    """)
