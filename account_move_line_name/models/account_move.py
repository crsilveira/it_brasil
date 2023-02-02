# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools.misc import formatLang, format_date


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self, invoice=False):
        result = super().action_post()
        recompute_payment_terms = False
        if self.document_number:
            for line in self.line_ids:
                if line.account_id.user_type_id.type in ('receivable', 'payable'):
                    if ((not line.name) or (
                        line.name and self.document_number not in line.name)):
                        recompute_payment_terms = True
        if recompute_payment_terms:
            self._recompute_payment_terms_lines()
        return result