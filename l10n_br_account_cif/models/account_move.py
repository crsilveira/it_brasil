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


    def _line_cost(self):
        # Hack: Na V14 o frete, seguro e outros custos não estão no lancamento contabil
        # e isto gera uma diferença entre o lancamento e o documento fiscal
        # Por ora incluimos linhas com estes valores no movimento
        # alterado = 0.0

        # se ja existe tem q excluir
        for line in self.line_ids:
            if line.name in ["[FREIGHT]", "[INSURANCE]", "[OTHER]"]:
                self.with_context(
                    check_move_validity=False,
                    skip_account_move_synchronization=True,
                    force_delete=True,
                ).write(
                    {
                        "line_ids": [(2, line.id)],
                        "to_check": False,
                    }
                )

        for line in self.line_ids:
            if not line.exclude_from_invoice_tab and line.freight_value > 0:
                new_line = self.env["account.move.line"].new(
                    {
                        "name": "[FREIGHT]",
                        "account_id": line.account_id.id,
                        "move_id": self.id,
                        "exclude_from_invoice_tab": True,
                        "price_unit": line.freight_value,
                    }
                )
                self.line_ids += new_line
                self.with_context(check_move_validity=False)._onchange_currency()
                # alterado += line.freight_value
            if not line.exclude_from_invoice_tab and line.insurance_value > 0:
                new_line = self.env["account.move.line"].new(
                    {
                        "name": "[INSURANCE]",
                        "account_id": line.account_id.id,
                        "move_id": self.id,
                        "exclude_from_invoice_tab": True,
                        "price_unit": line.insurance_value,
                    }
                )
                self.line_ids += new_line
                self.with_context(check_move_validity=False)._onchange_currency()
                # alterado += line.insurance_value
            if not line.exclude_from_invoice_tab and line.other_value > 0:
                new_line = self.env["account.move.line"].new(
                    {
                        "name": "[OTHER]",
                        "account_id": line.account_id.id,
                        "move_id": self.id,
                        "exclude_from_invoice_tab": True,
                        "price_unit": line.other_value,
                    }
                )
                self.line_ids += new_line
                self.with_context(check_move_validity=False)._onchange_currency()
                # alterado += line.other_value
        # if alterado:
        #     # estava dobrando o valor frete, seguro e outros no total
        #     import pudb;pu.db
        #     for line in self.line_ids:
        #         if line.product_id:                   
        #             if line.debit:
        #                 other = line.other_value + line.insurance_value + line.freight_value
        #                 line.with_context(check_move_validity=False).write({'debit': line.debit - other})
        #             if line.credit:
        #                 other = line.other_value + line.insurance_value + line.freight_value
        #                 line.with_context(check_move_validity=False).write({'credit': line.credit - other})

        #         if line.account_id.user_type_id.type == "receivable":
        #             line.with_context(check_move_validity=False).write({'debit': line.debit + alterado})
        #         if line.account_id.user_type_id.type == "payable":
        #             line.with_context(check_move_validity=False).write({'credit': line.credit + alterado})
        #     self._recompute_dynamic_lines(recompute_all_taxes=True)

    # @api.depends(
    #     'amount_other_value',
    # )
    # def _compute_amount(self):
    #     import pudb;pu.db
    #     result = super()._compute_amount()
    #     for record in self:
    #         record._line_cost()

    # def _compute_amount_others(self):
    #     total = 0.0
        
    #     for line in self.invoice_line_ids:
    #         total += line.amount_total

    #     if total:
    #         self.amount_total = total

    # @api.onchange("amount_freight_value")
    # def _onchange_amount_freight_value(self):
    #     if self.amount_freight_value:
    #         # import pudb;pu.db
    #         # for line in self.line_ids:
    #         #     if line.freight_value > 0:
    #         #         line.update({"freight_value": 0.0})
    #         # self._inverse_amount_freight()
    #         self._compute_amount()
    #         # self._compute_taxes_mapped()
    #     import pudb;pu.db
    #     for line in self.line_ids:
    #         if line.name == "[FREIGHT]":
    #             # line.with_context(check_move_validity=False, to_check=False).write(
    #             #     {
    #             #         "price_unit": line.freight_value,
    #             #     }
    #             # )
    #             self.with_context(
    #                 check_move_validity=False,
    #                 skip_account_move_synchronization=True,
    #                 force_delete=True,
    #             ).write(
    #                 {
    #                     "line_ids": [(2, line.id)],
    #                     "to_check": False,
    #                 }
    #             )
    #     for line in self.line_ids:
    #         import pudb
    #         if not line.exclude_from_invoice_tab and line.freight_value > 0:
    #             new_line = self.env["account.move.line"].new(
    #                 {
    #                     "name": "[FREIGHT]",
    #                     "account_id": line.account_id.id,
    #                     "move_id": self.id,
    #                     "exclude_from_invoice_tab": True,
    #                     "price_unit": line.freight_value,
    #                 }
    #             )
    #             self.line_ids += new_line
    #             self.with_context(check_move_validity=False)._onchange_currency()

    # @api.model_create_multi
    # def create(self, values):
    #     invoice = super().create(values)
    #     # import pudb;pu.db
    #     # for line in invoice.invoice_line_ids:
    #     #     line._onchange_fiscal_tax_ids()
    #     # invoice._finalize_invoices(invoice)
    #     # invoice._line_cost()
    #     # invoice._compute_amount()
    #     # invoice._compute_taxes_mapped()
    #     # invoice.with_context(check_move_validity=False)._onchange_currency()
    #     # import pudb;pu.db
    #     return invoice

    # def write(self, vals):
    #     import pudb;pu.db
    #     if (
    #         "amount_freight_value" in vals 
    #         or "amount_insurance_value" in vals
    #         or "amount_other_value" in vals
    #     ):
    #         self._line_cost()
    #     return super().write(vals)


    # def action_post(self):
    #     result = super().action_post()
    #     # self._line_cost()
    #     self.mapped("fiscal_document_id").filtered(
    #         lambda d: d.document_type_id
    #     ).action_document_confirm()

    #     return result

    # def button_draft(self): 
    #     # entrando com custos extras dos itens
    #     result = super().button_draft()

    #     # Hack: apagando linhas inseridas no lancamento para suportar as alteraçoes
    #     # na 14.0
    #     for line in self.line_ids:
    #         if line.name in ["[FREIGHT]", "[INSURANCE]", "[OTHER]"]:
    #             self.with_context(
    #                 check_move_validity=False,
    #                 skip_account_move_synchronization=True,
    #                 force_delete=True,
    #             ).write(
    #                 {
    #                     "line_ids": [(2, line.id)],
    #                     "to_check": False,
    #                 }
    #             )
    #     self.with_context(check_move_validity=False)._onchange_currency()

    #     return result