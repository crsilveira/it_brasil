# Copyright (C) 2009  Renato Lima - Akretion
# Copyright (C) 2012  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from functools import partial

from odoo import api, fields, models
from odoo.tools import float_is_zero
from odoo.tools.misc import formatLang
from collections import defaultdict

from ...l10n_br_fiscal.constants.fiscal import (
    CFOP_DESTINATION_EXPORT,
    FISCAL_IN
)


class AccountMove(models.Model):
    _inherit = "account.move"

    amount_freight_value = fields.Monetary(
        compute="_compute_freight_value",
        inverse="_inverse_amount_freight",
    )

    amount_insurance_value = fields.Monetary(
        compute="_compute_insurance_value",
        inverse="_inverse_amount_insurance",
    )

    amount_other_value = fields.Monetary(
        compute="_compute_other_value",
        inverse="_inverse_amount_other",
    )

    # Usado para tornar Somente Leitura os campos totais dos custos
    # de entrega quando a definição for por Linha
    delivery_costs = fields.Selection(
        related="company_id.delivery_costs",
    )

    @api.depends("amount_freight_value")
    def _compute_freight_value(self):
        total_freight = 0.0
        for record in self.invoice_line_ids:
            total_freight += record.freight_value
        self.amount_freight_value = total_freight

    @api.depends("amount_insurance_value")
    def _compute_insurance_value(self):
        total_insurance = 0.0
        for record in self.invoice_line_ids:
            total_insurance += record.insurance_value
        self.amount_insurance_value = total_insurance

    @api.depends("amount_other_value")
    def _compute_other_value(self):
        total_other = 0.0
        for record in self.invoice_line_ids:
            total_other += record.other_value
        self.amount_other_value = total_other

    def _inverse_amount_freight(self):
        # account_costs
        for record in self.filtered(lambda inv: inv.invoice_line_ids):
            if record.company_id.delivery_costs == "total":
                amount_freight_value = record.amount_freight_value
                if all(record.invoice_line_ids.mapped("freight_value")):
                    amount_freight_old = sum(record.invoice_line_ids.mapped("freight_value"))
                    for line in record.invoice_line_ids[:-1]:
                        line.freight_value = amount_freight_value * (
                            line.freight_value / amount_freight_old
                        )
                    record.invoice_line_ids[-1].freight_value = amount_freight_value - sum(
                        line.freight_value for line in record.invoice_line_ids[:-1]
                    )
                else:
                    amount_total = sum(record.invoice_line_ids.mapped("price_total"))
                    for line in record.invoice_line_ids[:-1]:
                        line.freight_value = amount_freight_value * (
                            line.price_total / amount_total
                        )
                    record.invoice_line_ids[-1].freight_value = amount_freight_value - sum(
                        line.freight_value for line in record.invoice_line_ids[:-1]
                    )
                for line in record.invoice_line_ids:
                    price_subtotal = line._get_price_total_and_subtotal()
                    line.price_subtotal = price_subtotal['price_subtotal']
                    line.update(line._get_fields_onchange_subtotal())
                    line._onchange_fiscal_taxes()
                record._recompute_dynamic_lines(recompute_all_taxes=True)
                record._fields["amount_total"].compute_value(record)

                record.write(
                    {
                        name: value
                        for name, value in record._cache.items()
                        if record._fields[name].compute == "_compute_amount"
                        and not record._fields[name].inverse
                    }
                )

    def _inverse_amount_insurance(self):
        for record in self.filtered(lambda inv: inv.invoice_line_ids):
            if record.company_id.delivery_costs == "total":
                amount_insurance_value = record.amount_insurance_value
                if all(record.invoice_line_ids.mapped("insurance_value")):
                    amount_insurance_old = sum(
                        record.invoice_line_ids.mapped("insurance_value")
                    )
                    for line in record.invoice_line_ids[:-1]:
                        line.insurance_value = amount_insurance_value * (
                            line.insurance_value / amount_insurance_old
                        )
                    record.invoice_line_ids[
                        -1
                    ].insurance_value = amount_insurance_value - sum(
                        line.insurance_value for line in record.invoice_line_ids[:-1]
                    )
                else:
                    amount_total = sum(record.invoice_line_ids.mapped("price_total"))
                    for line in record.invoice_line_ids[:-1]:
                        line.insurance_value = amount_insurance_value * (
                            line.price_total / amount_total
                        )
                    record.invoice_line_ids[
                        -1
                    ].insurance_value = amount_insurance_value - sum(
                        line.insurance_value for line in record.invoice_line_ids[:-1]
                    )

                for line in record.invoice_line_ids:
                    price_subtotal = line._get_price_total_and_subtotal()
                    line.price_subtotal = price_subtotal['price_subtotal']
                    line.update(line._get_fields_onchange_subtotal())
                    line._onchange_fiscal_taxes()
                record._recompute_dynamic_lines(recompute_all_taxes=True)

                record._fields["amount_total"].compute_value(record)
                record.write(
                    {
                        name: value
                        for name, value in record._cache.items()
                        if record._fields[name].compute == "_amount_all"
                        and not record._fields[name].inverse
                    }
                )

    def _inverse_amount_other(self):
        for record in self.filtered(lambda inv: inv.invoice_line_ids):
            if record.company_id.delivery_costs == "total":
                amount_other_value = record.amount_other_value
                if all(record.invoice_line_ids.mapped("other_value")):
                    amount_other_old = sum(record.invoice_line_ids.mapped("other_value"))
                    for line in record.invoice_line_ids[:-1]:
                        line.other_value = amount_other_value * (
                            line.other_value / amount_other_old
                        )
                    record.invoice_line_ids[-1].other_value = amount_other_value - sum(
                        line.other_value for line in record.invoice_line_ids[:-1]
                    )
                else:
                    amount_total = sum(record.invoice_line_ids.mapped("price_total"))
                    for line in record.invoice_line_ids[:-1]:
                        line.other_value = amount_other_value * (
                            line.price_total / amount_total
                        )
                    record.invoice_line_ids[-1].other_value = amount_other_value - sum(
                        line.other_value for line in record.invoice_line_ids[:-1]
                    )

                for line in record.invoice_line_ids:
                    price_subtotal = line._get_price_total_and_subtotal()
                    line.price_subtotal = price_subtotal['price_subtotal']
                    line.update(line._get_fields_onchange_subtotal())
                    line._onchange_fiscal_taxes()
                record._recompute_dynamic_lines(recompute_all_taxes=True)
                record._fields["amount_total"].compute_value(record)
                record.write(
                    {
                        name: value
                        for name, value in record._cache.items()
                        if record._fields[name].compute == "_amount_all"
                        and not record._fields[name].inverse
                    }
                )