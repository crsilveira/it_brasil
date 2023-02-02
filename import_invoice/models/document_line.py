from odoo.addons.spec_driven_model.models import spec_models


class NFeLine(spec_models.StackedModel):
    _name = "l10n_br_fiscal.document.line"
    _inherit = ["l10n_br_fiscal.document.line", "nfe.40.det"]
    _stacked = "nfe.40.det"
    _field_prefix = "nfe40_"
    _schema_name = "nfe"
    _schema_version = "4.0.0"
    _odoo_module = "l10n_br_nfe"
    _spec_module = "odoo.addons.l10n_br_nfe_spec.models.v4_00.leiauteNFe"
    _spec_tab_name = "NFe"
    _stack_skip = "nfe40_det_infNFe_id"
    _stacking_points = {}
    _force_stack_paths = ("det.imposto",)

    def _export_fields(self, xsd_fields, class_obj, export_dict):
        if class_obj._name == "nfe.40.prod":
            if self.account_line_ids.move_id.move_type == "in_invoice":
                vals_di_di = {
                    "nfe40_DI_prod_id": self.id,
                    "nfe40_nDI" : self.number_di,
                    "nfe40_dDI" : self.date_registration,
                    "nfe40_xLocDesemb" : self.location,
                    "nfe40_UFDesemb" : self.state_id.code,
                    "nfe40_dDesemb": self.date_release,
                    "nfe40_tpViaTransp" : self.type_transportation,
                    "nfe40_vAFRMM" : self.afrmm_value,
                    "nfe40_tpIntermedio" : self.tpIntermedio,
                    "nfe40_CNPJ" : self.thirdparty_cnpj,
                    "nfe40_UFTerceiro" : self.thirdparty_state_id.code,
                    "nfe40_cExportador" : self.exporting_code,
                }
               
                list_adi = []
                for line in self.di_ids:
                    vals_adi = {
                        "nfe40_nAdicao": line.name,
                        "nfe40_nSeqAdic": line.sequence_di,
                        "nfe40_cFabricante": line.manufacturer_code,
                        "nfe40_vDescDI": "{:.2f}".format(line.amount_discount) if line.amount_discount != 0.0 else False,
                        "nfe40_nDraw": line.drawback_number,
                    }
                    obj = self.env["nfe.40.adi"].create(vals_adi)
                    list_adi.append(obj.id)
                if len(list_adi):
                    vals_di_di["nfe40_adi"] = [(6, 0, list_adi)]                       
                    obj_di = self.env["nfe.40.di"].create(vals_di_di).id
                    self.nfe40_DI = [(6, 0, [obj_di])]

            if self.account_line_ids.move_id.move_type == "out_invoice":
                vals_di_di = {
                    "nfe40_detExport_prod_id": self.id,
                    "nfe40_nDraw": self.number_di
                }
                vals_adi = []
                for line in self.di_ids:
                    vals_adi = {
                        "nfe40_nRE": line.name,
                        "nfe40_chNFe": line.manufacturer_code,
                        "nfe40_qExport": "{:.2f}".format(line.amount_discount) if line.amount_discount != 0.0 else False,
                    }
                # TODO estou gravando so uma linha , se tiver mais vai dar erro
                if len(vals_adi):
                    export_id = self.env["nfe.40.exportind"].create(vals_adi)
                    vals_di_di["nfe40_exportInd"] = export_id.id                       
                    obj_di = self.env["nfe.40.detexport"].create(vals_di_di).id
                    self.nfe40_detExport = [(6, 0, [obj_di])]

        return super()._export_fields(xsd_fields, class_obj, export_dict)