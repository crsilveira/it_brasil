import re
import json
import requests
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        for move in self:
            if move.partner_id.country_id.code == 'BR':
                search_zip = self.env['l10n_br.zip'].search(
                    [('zip_code', '=', move.partner_id.zip.replace('-', ''))])
                self.zip_complete(move.partner_id, search_zip)

        return super(AccountMove, self).action_post()

    def consult_cnpj_zip(self, partner=None):
        _logger.info('Consultando CNPJ')
        cnpjws_url = 'https://publica.cnpj.ws/cnpj/'
        if partner and partner.company_type == 'company':
            if partner.cnpj_cpf:
                cnpj = re.sub('[^0-9]', '', partner.cnpj_cpf)
                response = requests.get(cnpjws_url + cnpj)
                cnpjws_result = json.loads(response.text)
                if response.status_code == 200:
                    _logger.info('CNPJ encontrado')
                    return cnpjws_result['estabelecimento']
                else:
                    _logger.info('CNPJ não encontrado')
                    return False
            else:
                _logger.info('Cliente sem CNPJ')
                return False
        else:
            _logger.info('Cliente não é uma empresa')
            return False

    def zip_complete(self, partner=None, search_zip=None):
        _logger.info('Preenchendo CEP')
        if partner:
            cnpj_zip = self.consult_cnpj_zip(partner)
            if cnpj_zip:
                cnpj_state = cnpj_zip['estado']
                cnpj_city = cnpj_zip['cidade']
                if not search_zip:
                    _logger.info('Criando CEP')
                    search_zip = self.env['l10n_br.zip'].create({
                        'zip_code': cnpj_zip['cep'],
                        'street_type': cnpj_zip['tipo_logradouro'],
                        'street_name': cnpj_zip['logradouro'],
                        'district': cnpj_zip['bairro'],
                        'country_id': self.env.ref('base.br').id,
                        'state_id': self.env['res.country.state'].search(
                            [('ibge_code', '=', cnpj_state['ibge_id'])]).id,
                        'city_id': self.env['res.city'].search(
                            [('ibge_code', '=', cnpj_city['ibge_id'])]).id,
                    })
                    self.update_zip_state_city(
                        search_zip, cnpj_state, cnpj_city)
                else:
                    _logger.info('Atualizando CEP')
                    search_zip.write({
                        'street_type': cnpj_zip['tipo_logradouro'],
                        'street_name': cnpj_zip['logradouro'],
                        'district': cnpj_zip['bairro'],
                        'country_id': self.env.ref('base.br').id,
                    })
                    self.update_zip_state_city(
                        search_zip, cnpj_state, cnpj_city)
            else:
                _logger.info('CNPJ não encontrado')

    def update_zip_state_city(self, search_zip, cnpj_state, cnpj_city):
        if not search_zip.state_id:
            _logger.info('Atualizando Estado')
            search_state = self.env['res.country.state'].search(
                [('ibge_code', '=', cnpj_state['ibge_id'])])
            if search_state:
                search_zip.write({
                    'state_id': search_state.id
                })

        if not search_zip.city_id:
            _logger.info('Atualizando Cidade')
            search_city = self.env['res.city'].search(
                [('ibge_code', '=', cnpj_city['ibge_id'])])
            if search_city:
                search_zip.write({
                    'city_id': search_city.id
                })

        return True
