from osv import osv
from osv import fields
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from datetime import datetime
import time

class Arrear_list(osv.osv):
    
    _name = 'arrear.list'
    
    def on_change_wakf_reg_no_to_arrear(self, cr, uid, ids, reg_no, context=None):
        values = {}
        values2 = {}
        invoice_lines1 = []
        invoice_lines2 = []
        id_res_partner = self.pool.get('res.partner')
        output = False
        if reg_no:
            search_condition = [('wakf_reg_no', '=', reg_no)]
            search_ids = id_res_partner.search(cr, uid, search_condition, context=context)
            similar_objs = id_res_partner.browse(cr, uid, search_ids, context=context)
            if similar_objs:
                output = id_res_partner.browse(cr, uid, search_ids, context=context)[0].id
                invoice_id = self.pool.get('account.invoice')
                search_condition = [('registration_no', '=', reg_no) , ('state','=','draft'),('assessment_type', '=', 'assessment'),('is_assessment','=',True)]
                search_condition2 = [('state','=','draft'),('registration_no', '=', reg_no),('assessment_type', '=', 'bj'),('is_assessment','=',True)]
                search_ids = self.pool.get('account.invoice').search(cr, uid, search_condition)
                search_ids2 = self.pool.get('account.invoice').search(cr, uid, search_condition2)
                if search_ids2:
                    for key in invoice_id.browse(cr,uid,search_ids2):
                        invoice_lines2.append((0,0,{'reg_no':key.registration_no,'account_year_line':key.assess_year_saleorder.id,'assessment_year_line':key.account_year_saleorder.id,'assess_amount':key.net_amount,'contri_amount1':key.amount_total}))
                    
                
                if search_ids:
                    for key in invoice_id.browse(cr,uid,search_ids):
                        invoice_lines1.append((0,0,{'reg_no':key.registration_no,'account_year_line':key.assess_year_saleorder.id,'assessment_year_line':key.account_year_saleorder.id,'assess_amount':key.net_amount,'contri_amount1':key.amount_total}))
                    
                    #return {'value' : values}
                if (not search_ids2) and (not search_ids):
                    search_condition = [('registration_no', '=', reg_no) , ('state','!=',"open")]
                    search_ids = self.pool.get('account.invoice').search(cr, uid, search_condition)
                    if search_ids:
                        invoice_lines1.append((2,0))
                        values={'arrear_line':invoice_lines1,}
                        return {'warning': {
                                            'title': _('Warning!'),
                                            'message':  _('No Arrears.Please Check Invoices For Confirmation'),},'value':values,
                                }
                    else:
                        invoice_lines1.append((2,0))
                        values={'arrear_line':invoice_lines1,}
                        return {'warning': {
                                            'title': _('Warning!'),
                                            'message':  _('No Invoice Generated For Specified Reg:no'),},'value':values,
                                }
                
                    #return {'value' : values}
                
                return {'value' : {'arrear_line':invoice_lines1+invoice_lines2,
                            'wakf_id':output,
                            }}
            else:
                return {'warning': {
                                            'title': _('Warning!'),
                                            'message':  _('No Wakf Generated For Specified Reg:no'),}
                        }
        else:
            invoice_lines1.append((2,0))
            values={'arrear_line':invoice_lines1,}
            return {'value' : values}
                                
    def on_change_all_wakf_arrear(self, cr, uid, ids,all_wakf):
        invoice_lines = []
        invoice_lines2 = []
        values = {}
        if all_wakf:
            invoice_id = self.pool.get('account.invoice')
            search_condition = [('state','=',"open"),('assessment_type', '=', 'assessment')] 
            search_condition2 = [('state','=','draft'),('assessment_type', '=', 'bj')]
            search_ids = self.pool.get('account.invoice').search(cr, uid, search_condition)
            search_ids2 = self.pool.get('account.invoice').search(cr, uid, search_condition2)
            if search_ids2:
                    for key in invoice_id.browse(cr,uid,search_ids2):
                        invoice_lines2.append((0,0,{'reg_no':key.registration_no,'account_year_line':key.assess_year_saleorder.id,'assessment_year_line':key.account_year_saleorder.id,'assess_amount':key.net_amount,'contri_amount1':key.amount_total}))
                    
            if search_ids:
                for key in invoice_id.browse(cr,uid,search_ids):            
                    invoice_lines.append((0,0,{'reg_no':key.registration_no,'account_year_line':key.assess_year_saleorder.id,'assessment_year_line':key.account_year_saleorder.id,'assess_amount':key.net_amount,'net_income1':key.net_amount,'contri_amount1':key.amount_total}))
               
                #return {'value' : values} 
            if (not search_ids2) and (not search_ids):
                invoice_lines.append((2,0))
                values={'arrear_line':invoice_lines}
                return {'warning': {
                                            'title': _('Warning!'),
                                            'message':  _('No Arrears Found.Check Invoice For Confirmation'),},'value':values,
                                }
            return {'value' :{ 'arrear_line':invoice_lines+invoice_lines2}}
                
                 
        else:
            invoice_lines.append((2,0))
            values = {'arrear_line':invoice_lines,                                            
                      }
            return {'value' : values}    
         
    def _total_amount_net_Assess(self, cr, uid, ids, field_name, arg, context=None):
        val1 = 0
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
            'total_income' : 0,
            }
            for line in order.arrear_line:
                val1 += line.assess_amount
            res[order.id]['net_income_assess']=val1          
        return res
    def _total_amount_contribution_arrear(self, cr, uid, ids, field_name, arg, context=None):
        val1 = 0
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
            'total_income' : 0,
            }
            for line in order.arrear_line:
                val1 += line.contri_amount1
            res[order.id]['contri_amount']=val1          
        return res
    
    _columns = {
             'reg_no':fields.integer('Registration No:',size=16),
             'wakf_id':fields.many2one('res.partner','Wakf Name'),                 
             'account_year':fields.date('Account Year'),
             'assessment_year':fields.date('Assessment Year'),
             'net_income_assess':fields.function(_total_amount_net_Assess,multi='sums2',string='Net Income(Assessment)',store=True),
             #'net_income':fields.function(_total_amount_net_bj,multi='sums',string='Net Income(BJ)',store=True), 
             'contri_amount':fields.function(_total_amount_contribution_arrear,multi='sums1',string='Total Contribution',store=True),
             'arrear_line':fields.one2many('arrear.line','arrear_line'),
             'user_id':fields.char('user id',size=16),
             'company_id': fields.many2one('res.company', 'Company', required=False),
             'all_wakf':fields.boolean('ALL'),
        }
    
    _defaults={
        'user_id': lambda obj, cr, uid, context: uid,
        'company_id': lambda self,cr,uid,ctx: self.pool['res.company']._company_default_get(cr,uid,object='arrear.list',context=ctx)
     }
Arrear_list()


class Arrear_line(osv.osv):

    _name = 'arrear.line'
 
    _columns = {
                
         'reg_no':fields.integer('Register No',size=8),
         'arrear_line':fields.many2one('arrear.list','Arrear Line',ondelete='set null',required=False),
         'account_year_line':fields.many2one('account.fiscalyear','Account Year',ondelete='set null'),
         'assessment_year_line':fields.many2one('account.fiscalyear','Assessment Year',ondelete='set null'),
         'assess_amount':fields.float('Assessment Amount',size=16),
         #'net_income1':fields.float('BJ Amount',size=16), 
         'contri_amount1':fields.float('Contribution',size=16),  
                                        
                }
        
Arrear_line()