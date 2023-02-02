# Copyright (C) 2022 - TODAY Renan Teixeira - IT Brasil
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Consulta CNPJ",
    "summary": "Consulta de CNPJ com base em dados públicos",
    "category": "Localization",
    "license": "AGPL-3",
    "author": "IT Brasil",
    "maintainers": ["renanteixeira", "it-brasil"],
    "website": "https://github.com/it-brasil/it_brasil",
    "version": "14.0.2.2.1",
    "depends": ["l10n_br_base"],
    "data": [
        'security/ir.model.access.csv',
        'views/res_partner.xml'
    ],
    "demo": [],
    "installable": True,
    "development_status": "Production/Stable",
}
