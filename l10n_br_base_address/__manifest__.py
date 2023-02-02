# Copyright (C) 2022 - TODAY Renan Teixeira - IT Brasil
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Fix Contacts Addresses",
    "summary": "Fix Contacts Addresses view",
    "category": "Extra Tools",
    "license": "AGPL-3",
    "author": "IT Brasil",
    "maintainers": ["renanteixeira", "it-brasil"],
    "website": "https://itbrasil.com.br",
    "version": "14.0.1.0.0",
    "depends": ["base_address_city", "base_address_extended", "l10n_br_base", "l10n_br_zip"],
    "data": [
        "data/ir.ui.view.csv",
        "views/res_partner_address_view.xml",
    ],
    "demo": [],
    "installable": True,
    "development_status": "Mature",
    "external_dependencies": {},
}
