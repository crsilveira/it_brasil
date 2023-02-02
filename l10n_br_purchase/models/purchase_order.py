# Copyright (C) 2009  Renato Lima - Akretion, Gabriel C. Stabel
# Copyright (C) 2012  Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import api, fields, models

# from odoo.addons.l10n_br_fiscal.constants.fiscal import DOCUMENT_ISSUER_PARTNER


class PurchaseOrder(models.Model):
    _name = "purchase.order"
    _inherit = [_name, "l10n_br_fiscal.document.mixin"]

    @api.model
    def _default_fiscal_operation(self):
        return self.env.company.purchase_fiscal_operation_id

    @api.model
    def _fiscal_operation_domain(self):
        domain = [
            ("state", "=", "approved"),
            ("fiscal_type", "in", ("purchase", "other", "purchase_refund")),
        ]
        return domain

    fiscal_operation_id = fields.Many2one(
        comodel_name="l10n_br_fiscal.operation",
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=_default_fiscal_operation,
        domain=lambda self: self._fiscal_operation_domain(),
    )

    cnpj_cpf = fields.Char(
        string="CNPJ/CPF",
        related="partner_id.cnpj_cpf",
    )

    legal_name = fields.Char(
        string="Legal Name",
        related="partner_id.legal_name",
    )

    ie = fields.Char(
        string="State Tax Number/RG",
        related="partner_id.inscr_est",
    )

    comment_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.comment",
        relation="purchase_order_comment_rel",
        column1="purchase_id",
        column2="comment_id",
        string="Comments",
    )

    # amount_freight_value = fields.Monetary(
    #     inverse="_inverse_amount_freight",
    # )

    # amount_insurance_value = fields.Monetary(
    #     inverse="_inverse_amount_insurance",
    # )

    # amount_other_value = fields.Monetary(
    #     inverse="_inverse_amount_other",
    # )

    # def _inverse_amount_freight(self):
    #     for record in self.filtered(lambda so: so.order_line):
    #         if record.company_id.delivery_costs == "total":
    #             amount_freight_value = record.amount_freight_value
    #             if all(record.order_line.mapped("freight_value")):
    #                 amount_freight_old = sum(record.order_line.mapped("freight_value"))
    #                 for line in record.order_line[:-1]:
    #                     line.freight_value = amount_freight_value * (
    #                         line.freight_value / amount_freight_old
    #                     )
    #                 record.order_line[-1].freight_value = amount_freight_value - sum(
    #                     line.freight_value for line in record.order_line[:-1]
    #                 )
    #             else:
    #                 amount_total = sum(record.order_line.mapped("price_total"))
    #                 for line in record.order_line[:-1]:
    #                     line.freight_value = amount_freight_value * (
    #                         line.price_total / amount_total
    #                     )
    #                 record.order_line[-1].freight_value = amount_freight_value - sum(
    #                     line.freight_value for line in record.order_line[:-1]
    #                 )
    #             for line in record.order_line:
    #                 line._onchange_fiscal_taxes()
    #             record._fields["amount_total"].compute_value(record)
    #             record.write(
    #                 {
    #                     name: value
    #                     for name, value in record._cache.items()
    #                     if record._fields[name].compute == "_amount_all"
    #                     and not record._fields[name].inverse
    #                 }
    #             )

    # def _inverse_amount_insurance(self):
    #     for record in self.filtered(lambda so: so.order_line):
    #         if record.company_id.delivery_costs == "total":

    #             amount_insurance_value = record.amount_insurance_value
    #             if all(record.order_line.mapped("insurance_value")):
    #                 amount_insurance_old = sum(
    #                     record.order_line.mapped("insurance_value")
    #                 )
    #                 for line in record.order_line[:-1]:
    #                     line.insurance_value = amount_insurance_value * (
    #                         line.insurance_value / amount_insurance_old
    #                     )
    #                 record.order_line[
    #                     -1
    #                 ].insurance_value = amount_insurance_value - sum(
    #                     line.insurance_value for line in record.order_line[:-1]
    #                 )
    #             else:
    #                 amount_total = sum(record.order_line.mapped("price_total"))
    #                 for line in record.order_line[:-1]:
    #                     line.insurance_value = amount_insurance_value * (
    #                         line.price_total / amount_total
    #                     )
    #                 record.order_line[
    #                     -1
    #                 ].insurance_value = amount_insurance_value - sum(
    #                     line.insurance_value for line in record.order_line[:-1]
    #                 )
    #             for line in record.order_line:
    #                 line._onchange_fiscal_taxes()
    #             record._fields["amount_total"].compute_value(record)
    #             record.write(
    #                 {
    #                     name: value
    #                     for name, value in record._cache.items()
    #                     if record._fields[name].compute == "_amount_all"
    #                     and not record._fields[name].inverse
    #                 }
    #             )

    # def _inverse_amount_other(self):
    #     for record in self.filtered(lambda so: so.order_line):
    #         if record.company_id.delivery_costs == "total":
    #             amount_other_value = record.amount_other_value
    #             if all(record.order_line.mapped("other_value")):
    #                 amount_other_old = sum(record.order_line.mapped("other_value"))
    #                 for line in record.order_line[:-1]:
    #                     line.other_value = amount_other_value * (
    #                         line.other_value / amount_other_old
    #                     )
    #                 record.order_line[-1].other_value = amount_other_value - sum(
    #                     line.other_value for line in record.order_line[:-1]
    #                 )
    #             else:
    #                 amount_total = sum(record.order_line.mapped("price_total"))
    #                 for line in record.order_line[:-1]:
    #                     line.other_value = amount_other_value * (
    #                         line.price_total / amount_total
    #                     )
    #                 record.order_line[-1].other_value = amount_other_value - sum(
    #                     line.other_value for line in record.order_line[:-1]
    #                 )
    #             for line in record.order_line:
    #                 line._onchange_fiscal_taxes()
    #             record._fields["amount_total"].compute_value(record)
    #             record.write(
    #                 {
    #                     name: value
    #                     for name, value in record._cache.items()
    #                     if record._fields[name].compute == "_amount_all"
    #                     and not record._fields[name].inverse
    #                 }
    #             )

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):

        order_view = super().fields_view_get(view_id, view_type, toolbar, submenu)

        if view_type == "form":

            view = self.env["ir.ui.view"]

            sub_form_view = order_view["fields"]["order_line"]["views"]["form"]["arch"]

            sub_form_node = self.env["purchase.order.line"].inject_fiscal_fields(
                sub_form_view
            )

            sub_arch, sub_fields = view.postprocess_and_fields(
                sub_form_node, "purchase.order.line", False
            )

            order_view["fields"]["order_line"]["views"]["form"] = {
                "fields": sub_fields,
                "arch": sub_arch,
            }

        return order_view

    # TODO open by default Invoice view with Fiscal Details Button
    # You can add a group to select default view Fiscal Invoice or
    # Account invoice.
    # def action_view_invoice(self):
    #     result = super().action_view_invoice()
    #     fiscal_dict = self._prepare_br_fiscal_dict(default=True)
    #
    #     document_type_id = self._context.get('document_type_id')
    #
    #     if document_type_id:
    #         document_type = self.env['l10n_br_fiscal.document.type'].browse(
    #             document_type_id)
    #     else:
    #         document_type = self.company_id.document_type_id
    #         document_type_id = self.company_id.document_type_id.id
    #
    #     fiscal_dict['default_document_type_id'] = document_type_id
    #     document_serie = document_type.get_document_serie(
    #         self.company_id, self.fiscal_operation_id)
    #
    #     if document_serie:
    #         fiscal_dict['default_document_serie_id'] = document_serie.id
    #
    #     fiscal_dict['default_issuer'] = DOCUMENT_ISSUER_PARTNER
    #
    #     if self.fiscal_operation_id and self.fiscal_operation_id.journal_id:
    #         fiscal_dict['default_journal_id'] = (
    #             self.fiscal_operation_id.journal_id.id)
    #
    #     result['context'].update(fiscal_dict)
    #     return result

    @api.onchange("fiscal_operation_id")
    def _onchange_fiscal_operation_id(self):
        self.fiscal_position_id = self.fiscal_operation_id.fiscal_position_id

    def _get_amount_lines(self):
        """Get object lines instaces used to compute fields"""
        return self.mapped("order_line")

    @api.depends("order_line")
    def _compute_amount(self):
        return super()._compute_amount()

    @api.depends("order_line.price_total")
    def _amount_all(self):
        self._compute_amount()
        # super()._amount_all()

    def _prepare_invoice(self):
        self.ensure_one()
        invoice_vals = super()._prepare_invoice()
        invoice_vals.update(
            {
                "fiscal_operation_id": self.fiscal_operation_id.id,
                "document_type_id": self.company_id.document_type_id.id,
            }
        )
        return invoice_vals

    # def _amount_by_group(self):
    #     for order in self:
    #         currency = order.currency_id or order.company_id.currency_id
    #         fmt = partial(
    #             formatLang,
    #             self.with_context(lang=order.partner_id.lang).env,
    #             currency_obj=currency,
    #         )
    #         res = {}
    #         for line in order.order_line:
    #             taxes = line._compute_taxes(line.fiscal_tax_ids)["taxes"]
    #             for tax in line.fiscal_tax_ids:
    #                 computed_tax = taxes.get(tax.tax_domain)
    #                 pr = order.currency_id.rounding
    #                 if computed_tax and not float_is_zero(
    #                     computed_tax.get("tax_value", 0.0), precision_rounding=pr
    #                 ):
    #                     group = tax.tax_group_id
    #                     res.setdefault(group, {"amount": 0.0, "base": 0.0})
    #                     res[group]["amount"] += computed_tax.get("tax_value", 0.0)
    #                     res[group]["base"] += computed_tax.get("base", 0.0)
    #         res = sorted(res.items(), key=lambda l: l[0].sequence)
    #         order.amount_by_group = [
    #             (
    #                 line[0].name,
    #                 line[1]["amount"],
    #                 line[1]["base"],
    #                 fmt(line[1]["amount"]),
    #                 fmt(line[1]["base"]),
    #                 len(res),
    #             )
    #             for line in res
    #         ]
