# Copyright 2022 Lucas Avila
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Declaração de Importação e Importar XML de NF-e",
    "description": """Importar Faturas""",
    "version": "14.0.2.0.0",
    "license": "AGPL-3",
    "author": "Lucas Avila, IT Brasil",
    "website": "https://itbrasil.com.br",
    "category": "Accounting",
    "depends": [
            "base", 
            "l10n_br_nfe",
            "l10n_br_purchase", 
        ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/purchase_order.xml",
        "wizard/account_import_nfe.xml",
        "views/l10n_br_layout.xml",
    ],
    "demo": [],
    "application": False,
}
