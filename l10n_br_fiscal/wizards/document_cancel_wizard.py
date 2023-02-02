# Copyright 2019 KMEE
# Copyright (C) 2020  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models
import logging
_logger = logging.getLogger(__name__)


class DocumentCancelWizard(models.TransientModel):
    _name = "l10n_br_fiscal.document.cancel.wizard"
    _description = "Fiscal Document Cancel Wizard"
    _inherit = "l10n_br_fiscal.base.wizard.mixin"

    def do_cancel(self):
        self.document_id._document_cancel(self.justification)

    def doit(self):
        if self.justification != False:
            if len(self.justification) < 15:
                raise models.ValidationError("A justificativa deve ter no mínimo 15 caracteres.")
        else:
            raise models.ValidationError("A justificativa é obrigatória.")
        for wizard in self:
            if wizard.document_id:
                wizard.do_cancel()
        self._close()
