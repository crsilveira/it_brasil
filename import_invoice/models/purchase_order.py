from odoo import models

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    #if partner is not from Brazil, prepare invoice values with issuer equals "company" and document serie from company
    def _prepare_invoice(self):
        res = super(PurchaseOrder, self)._prepare_invoice()
        if self.partner_id.country_id.code != "BR":
            res["issuer"] = "company"
            res["document_serie_id"] = self.company_id.nfe_default_serie_id.id
        return res

    # def action_create_invoice(self):
    #     res = super(PurchaseOrder, self).action_create_invoice()
    #     #invoice = max([inv.id for inv in self.invoice_ids])
    #     return res

    # TODO
    def import_di(self):
        return
