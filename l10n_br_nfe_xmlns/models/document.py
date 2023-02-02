# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import pytz
import base64
import logging
import re
import io
from datetime import datetime
from io import StringIO
from unicodedata import normalize

from erpbrasil.assinatura import certificado as cert
from erpbrasil.base.fiscal.edoc import ChaveEdoc
from erpbrasil.edoc.nfe import NFe as edoc_nfe
from erpbrasil.edoc.pdf import base
from erpbrasil.transmissao import TransmissaoSOAP
from lxml import etree
from nfelib.v4_00 import leiauteNFe_sub as nfe_sub, retEnviNFe as leiauteNFe
from requests import Session

from odoo.addons.l10n_br_nfe.models.danfe import danfe
from lxml import etree

from odoo import _, api, fields
from odoo.exceptions import UserError, ValidationError

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    AUTORIZADO,
    CANCELADO,
    CANCELADO_DENTRO_PRAZO,
    CANCELADO_FORA_PRAZO,
    DENEGADO,
    DOCUMENT_ISSUER_COMPANY,
    EVENT_ENV_HML,
    EVENT_ENV_PROD,
    EVENTO_RECEBIDO,
    LOTE_PROCESSADO,
    MODELO_FISCAL_NFCE,
    MODELO_FISCAL_NFE,
    PROCESSADOR_OCA,
    SITUACAO_EDOC_AUTORIZADA,
    SITUACAO_EDOC_CANCELADA,
    SITUACAO_EDOC_DENEGADA,
    SITUACAO_EDOC_REJEITADA,
    SITUACAO_FISCAL_CANCELADO,
    SITUACAO_FISCAL_CANCELADO_EXTEMPORANEO,
)
from odoo.addons.spec_driven_model.models import spec_models

from odoo.addons.l10n_br_nfe.constants.nfe import (
    NFCE_DANFE_LAYOUTS,
    NFE_DANFE_LAYOUTS,
    NFE_ENVIRONMENTS,
    NFE_TRANSMISSIONS,
    NFE_VERSIONS,
)

_logger = logging.getLogger(__name__)


def filter_processador_edoc_nfe(record):
    if record.processador_edoc == PROCESSADOR_OCA and record.document_type_id.code in [
        MODELO_FISCAL_NFE,
        MODELO_FISCAL_NFCE,
    ]:
        return True
    return False


class NFe(spec_models.StackedModel):
    _inherit = "l10n_br_fiscal.document"


    def atualiza_status_nfe(self, infProt, xml_file):
        self.ensure_one()
        # TODO: Verificar a consulta de notas
        # if not infProt.chNFe == self.key:
        #     self = self.search([
        #         ('key', '=', infProt.chNFe)
        #     ])
        if infProt.cStat in AUTORIZADO:
            state = SITUACAO_EDOC_AUTORIZADA
        elif infProt.cStat in DENEGADO:
            state = SITUACAO_EDOC_DENEGADA
        else:
            state = SITUACAO_EDOC_REJEITADA
        # acrescenta a tag <?xml .. encoding=...> no xml final
        root = etree.fromstring(xml_file)
        file = etree.tostring(root,
            pretty_print=True,
            xml_declaration=True,
            encoding='UTF-8')
        xml_file = file.decode("utf-8")
        if self.authorization_event_id and infProt.nProt:
            if type(infProt.dhRecbto) == datetime:
                protocol_date = fields.Datetime.to_string(infProt.dhRecbto)
            else:
                protocol_date = fields.Datetime.to_string(
                    datetime.fromisoformat(infProt.dhRecbto)
                )

            self.authorization_event_id.set_done(
                status_code=infProt.cStat,
                response=infProt.xMotivo,
                protocol_date=protocol_date,
                protocol_number=infProt.nProt,
                file_response_xml=xml_file,
            )
        self.write(
            {
                "status_code": infProt.cStat,
                "status_name": infProt.xMotivo,
            }
        )
        self._change_state(state)

    def _eletronic_document_send(self):
        # super(NFe, self)._eletronic_document_send()
        for record in self.filtered(filter_processador_edoc_nfe):
            record._export_fields_pagamentos()
            record._export_fields_faturas()
            if self.xml_error_message:
                return
            processador = record._processador()
            for edoc in record.serialize():
                processo = None
                for p in processador.processar_documento(edoc):
                    processo = p
                    if processo.webservice == "nfeAutorizacaoLote":
                        record.authorization_event_id._save_event_file(
                            processo.envio_xml.decode("utf-8"), "xml"
                        )

            if processo.resposta.cStat in LOTE_PROCESSADO + ["100"]:
                if (hasattr(processo, 'protocolo')):
                    xml_file = processo.processo_xml.decode("utf-8")
                    xml_file = xml_file.replace('<NFe>', '<NFe xmlns="http://www.portalfiscal.inf.br/nfe">')
                    record.atualiza_status_nfe(
                        processo.protocolo.infProt, xml_file
                    )

                elif processo.resposta.protNFe.infProt.cStat in AUTORIZADO:
                    # Qdo a NFe ja foi enviada e deu algum erro no retorno
                    # qdo tenta enviar novamente entra aqui.
                    if not self.authorization_file_id:
                        arquivo = self.send_file_id
                        xml_string = base64.b64decode(arquivo.datas).decode()
                        root = etree.fromstring(xml_string)
                        ns = {None: "http://www.portalfiscal.inf.br/nfe"}
                        new_root = etree.Element("nfeProc", nsmap=ns)

                        protNFe_node = etree.Element("protNFe")
                        infProt = etree.SubElement(protNFe_node, "infProt")
                        etree.SubElement(infProt, "tpAmb").text = processo.resposta.protNFe.infProt.tpAmb
                        etree.SubElement(infProt, "verAplic").text = processo.resposta.protNFe.infProt.verAplic
                        etree.SubElement(infProt, "dhRecbto").text = fields.Datetime.to_string(
                            processo.resposta.protNFe.infProt.dhRecbto)
                        etree.SubElement(infProt, "nProt").text = processo.resposta.protNFe.infProt.nProt
                        # etree.SubElement(infProt, "digVal").text = processo.resposta.protNFe.infProt.digVal
                        etree.SubElement(infProt, "cStat").text = processo.resposta.protNFe.infProt.cStat
                        etree.SubElement(infProt, "xMotivo").text = processo.resposta.protNFe.infProt.xMotivo

                        new_root.append(root)
                        new_root.append(protNFe_node)
                        file = etree.tostring(new_root)
                        file = file.decode("utf-8")
                        file = file.replace('<NFe>', '<NFe xmlns="http://www.portalfiscal.inf.br/nfe">')

                        record.atualiza_status_nfe(
                            processo.resposta.protNFe.infProt, file
                        )
                    try:
                        record.make_pdf()
                    except Exception as e:
                        # Não devemos interromper o fluxo
                        # E dar rollback em um documento
                        # autorizado, podendo perder dados.
                        # Se der problema que apareça quando
                        # o usuário clicar no gera PDF novamente.
                       _logger.error("DANFE Error \n {}".format(e))
                else:
                    # Entra aqui qdo a nota ja foi enviada
                    # TODO : na verdade era pra dar erro de Duplicidade
                    raise UserError(_("Número de Nota já existente no SEFAZ."))

            elif processo.resposta.cStat == "225":
                state = SITUACAO_EDOC_REJEITADA

                self._change_state(state)

                self.write(
                    {
                        "status_code": processo.resposta.cStat,
                        "status_name": processo.resposta.xMotivo,
                    }
                )
        return

    def make_pdf(self):
        if not self.filtered(filter_processador_edoc_nfe):
            return super().make_pdf()

        file_pdf = self.file_report_id
        self.file_report_id = False
        file_pdf.unlink()

        if self.authorization_file_id:
            arquivo = self.authorization_file_id
            xml_string = base64.b64decode(arquivo.datas).decode()
        else:
            arquivo = self.send_file_id
            xml_string = base64.b64decode(arquivo.datas).decode()
            xml_string = self.temp_xml_autorizacao(xml_string)

        # Teste Usando impressao via ReportLab Pytrustnfe
        evento_xml = []
        cce_list = self.env['l10n_br_fiscal.event'].search([
            ('type', '=', '14'),
            ('document_id', '=', self.id),
        ])

        if cce_list:
            for cce in cce_list:
                cce_xml = base64.b64decode(cce.file_request_id.datas)
                evento_xml.append(etree.fromstring(cce_xml))

        logo = base64.b64decode(self.company_id.logo)

        tmpLogo = io.BytesIO()
        tmpLogo.write(logo)
        tmpLogo.seek(0)

        timezone = pytz.timezone(self.env.context.get('tz') or 'UTC')
        # alterado para exibir o arquivo xml com a tag <?xml ...encoding=...>
        xml_element = etree.fromstring(bytes(xml_string, encoding='utf8'))

        cancel_list = self.env['l10n_br_fiscal.event'].search([
            ('type', '=', '2'),
            ('document_id', '=', self.id),
        ])
        if cancel_list:
            cancel_xml = base64.b64decode(cancel_list.file_request_id.datas).decode()
            evento_xml.append(etree.fromstring(cancel_xml))

        oDanfe = danfe(list_xml=[xml_element], logo=tmpLogo,
            evento_xml=evento_xml, timezone=timezone)
        tmpDanfe = io.BytesIO()
        oDanfe.writeto_pdf(tmpDanfe)
        danfe_file = tmpDanfe.getvalue()
        tmpDanfe.close()

        # base64.b64encode(bytes(tmpDanfe)),

        self.file_report_id = self.env["ir.attachment"].create(
            {
                "name": self.document_key + ".pdf",
                "res_model": self._name,
                "res_id": self.id,
                "datas": base64.b64encode(danfe_file),
                "mimetype": "application/pdf",
                "type": "binary",
            }
        )
