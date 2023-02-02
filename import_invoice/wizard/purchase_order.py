from datetime import datetime, timedelta
import logging
import base64
import xml.etree.ElementTree as ET
from odoo import fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

notification = {
    "type": "ir.actions.client",
    "tag": "display_notification",
    "params": {"next": {"type": "ir.actions.act_window_close"}},
}

class PurchaseOrderWizard(models.TransientModel):
    _name = "purchase.order.wizard"

    xml_invoice = fields.Binary(required=True)

    def import_invoice(self):
        base = base64.b64decode(self.xml_invoice).decode('UTF-8')
        root =  ET.ElementTree(ET.fromstring(base)).getroot()
        cnpj_emit = root.find(".//{http://www.portalfiscal.inf.br/nfe}emit/{http://www.portalfiscal.inf.br/nfe}CNPJ").text
        
        purchase = self.env["purchase.order"].browse(self._context.get("active_id"))
        cnpj_fornecedor = self.clear_cnpj(purchase.partner_id.cnpj_cpf) if purchase.partner_id.cnpj_cpf else False
        cnpj_xml = self.clear_cnpj(cnpj_emit)

        if cnpj_fornecedor != cnpj_xml:
            raise UserError(_("O CNPJ do emitente não é igual ao CNPJ do parceiro do pedido de compras"))

        itens =  {}
        search_itens = ["nNF", "chNFe","serie","nProt","finNFe", "dhRecbto","dhEmi","vNF", "cStat", "xMotivo"]

        for item in search_itens:
            src = root.find(".//{http://www.portalfiscal.inf.br/nfe}"+ item).text
            if item in ["dhRecbto","dhEmi"]:
                src = src.replace("T"," ").replace("-03:00","")
            itens[item] = src
        
        vals = {
            "document_number": itens["nNF"],
            "document_key": itens["chNFe"],
            "document_serie": itens["serie"],
            "authorization_protocol": itens["nProt"],
            "invoice_date": itens["dhEmi"],
            "date": itens["dhEmi"],
            "authorization_date": itens["dhRecbto"],
            "edoc_purpose": itens["finNFe"],
        } 

        # Verifica 1 centavo a mais ou a menos
        one_cent_dif = False
        if (round(float(itens["vNF"]) - purchase.amount_total, 2) == 0.01 
         or round(purchase.amount_total - float(itens["vNF"]), 2) == 0.01):
            one_cent_dif = True

        if "{:.2f}".format(purchase.amount_total) != itens["vNF"] and not one_cent_dif:
            vals_activity = {
                "summary": f"Valores Divergentes (PO {purchase.name})",
                "note": f"Valor total do xml difere do total do pedido de compras (PO {purchase.name})" +
                        f"<br><br> Número da nota: {itens['nNF']} <br>Chave da nota: {itens['chNFe']}" + 
                        f"<br>Valor da nota: {itens['vNF']}  | Valor do pedido: {'{:.2f}'.format(purchase.amount_total)}",
                "date_deadline": datetime.today(),
                "user_id": purchase.user_id.id or 1,
                "activity_type_id": 4,
                "res_model_id": self.env["ir.model"].search([("model","=","purchase.order")]).id,
                "res_id": purchase.id,
            }
            self.env["mail.activity"].create(vals_activity)
            notification["params"].update(
                {
                    "title": _("Atenção"),
                    "message": _("Valor total do xml difere do total do pedido de compras, uma atividade foi aberta para que isso seja analisado"),
                    "type": "warning",
                }
            )
            return notification
        invoice_id = purchase.action_create_invoice()
        invoice_eletronic = self.env["account.move"].browse(invoice_id['res_id'])
        invoice_eletronic.write(vals)
        # invoice_eletronic.authorization_event_id.set_done(
        #         status_code=itens["cStat"],
        #         response=itens["xMotivo"],
        #         protocol_date=itens["dhRecbto"],
        #         protocol_number=itens["nProt"],
        #         file_response_xml=base,
        #     )
        return invoice_id

    def clear_cnpj(self, cnpj):
        return cnpj.replace(".","").replace("/","").replace("-","")

