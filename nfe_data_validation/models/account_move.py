#
#    Copyright © 2022–; Brasil; IT Brasil; Todos os direitos reservados
#    Copyright © 2022–; Brazil; IT Brasil; All rights reserved
#

from odoo import api, fields, models

class AccountMove(models.Model):
	_inherit = 'account.move'

	def action_post(self):
		#self.ensure_one()
		document = self.fiscal_document_id
		document.valida_dados_remetente()
		document.valida_dados_destinatario()
		document.valida_endereco_entrega()
		document.valida_dados_produtos()
		return super().action_post() 
