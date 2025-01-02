## Permanent GeoCat background override

The SCSS in this folder (and the SVG files in the `static/img` folder) is used to "permanently" override the Odoo Enterprise background
that is set in the `web_enterprise/static/src/webclient/home_menu` folder of the Odoo enterprise installation. 

In the `__manifest__.py` file, the `web.assets_frontend`, `web.assets_backend` (and respective `web.assets_web_dark` for the dark theme)
include replacements for the `web_enterprise` assets.