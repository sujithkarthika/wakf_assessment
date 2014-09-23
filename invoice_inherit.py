from osv import osv
from osv import fields
from tools.translate import _
import addons.decimal_precision as dp
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from datetime import date

import time

from lxml import etree

class invoice_inherit(osv.osv):
    
    _inherit = 'account.invoice'
    ########################################## UPDATES ###############################################
    ###################################################################################################
    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        journal_obj = self.pool.get('account.journal')
        if context is None:
            context = {}

        if context.get('active_model', '') in ['res.partner'] and context.get('active_ids', False) and context['active_ids']:
            partner = self.pool.get(context['active_model']).read(cr, uid, context['active_ids'], ['supplier','customer'])[0]
            if not view_type:
                view_id = self.pool.get('ir.ui.view').search(cr, uid, [('name', '=', 'account.invoice.tree')])
                view_type = 'tree'
            if view_type == 'form':
                if partner['supplier'] and not partner['customer']:
                    view_id = self.pool.get('ir.ui.view').search(cr,uid,[('name', '=', 'account.invoice.supplier.form')])
                elif partner['customer'] and not partner['supplier']:
                    view_id = self.pool.get('ir.ui.view').search(cr,uid,[('name', '=', 'account.invoice.form')])
        if view_id and isinstance(view_id, (list, tuple)):
            view_id = view_id[0]
        res = super(invoice_inherit,self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)

        type = context.get('journal_type', False)
        for field in res['fields']:
            if field == 'journal_id' and type:
                journal_select = journal_obj._name_search(cr, uid, '', [('type', '=', type)], context=context, limit=None, name_get_uid=1)
                res['fields'][field]['selection'] = journal_select

        doc = etree.XML(res['arch'])

        if context.get('type', False):
            for node in doc.xpath("//field[@name='partner_bank_id']"):
                if context['type'] == 'in_refund':
                    node.set('domain', "[('partner_id.ref_companies', 'in', [company_id])]")
                elif context['type'] == 'out_refund':
                    node.set('domain', "[('partner_id', '=', partner_id)]")
            res['arch'] = etree.tostring(doc)

        if view_type == 'search':
            if context.get('type', 'in_invoice') in ('out_invoice', 'out_refund'):
                for node in doc.xpath("//group[@name='extended filter']"):
                    doc.remove(node)
                for node in doc.xpath("//field[@string='Application Number']"):
                    doc.remove(node)
            if context.get('type', 'out_invoice') in ('in_invoice', 'in_refund'):
                for node in doc.xpath("//field[@string='Register Number']"):
                    doc.remove(node)
            res['arch'] = etree.tostring(doc)

        if view_type == 'tree':
            partner_string = _('Wakf Name')
            if context.get('type', 'out_invoice') in ('in_invoice', 'in_refund'):
                partner_string = _('Applicant Name')
                for node in doc.xpath("//field[@name='reference']"):
                    node.set('invisible', '0')
            for node in doc.xpath("//field[@name='partner_id']"):
                node.set('string', partner_string)
                if partner_string == 'Applicant Name':
                    for node in doc.xpath("//field[@name='registration_no']"):
                        node.set('invisible', 'True')
                        doc.remove(node)
                if partner_string == 'Wakf Name':
                    for node in doc.xpath("//field[@name='appli_no']"):
                        node.set('invisible', 'True')
                        doc.remove(node)
            res['arch'] = etree.tostring(doc)
        return res
    
    def _amount_all(self, cr, uid, ids, name, args, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            res[invoice.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
                'net_amount':0.0
            }
            for line in invoice.invoice_line:
                res[invoice.id]['amount_untaxed'] += line.price_subtotal
                res[invoice.id]['net_amount'] += line.new_amount           
            for line in invoice.tax_line:
                res[invoice.id]['amount_tax'] += line.amount              
            res[invoice.id]['amount_total'] = ( res[invoice.id]['amount_tax'] + res[invoice.id]['amount_untaxed'] )   
        return res
    def _deflt_ass_year(self, cr, uid, ids, context=None):
        res ={}
        today = date.today()
        month_of = today.month
        if month_of <= 3:
            date_of = '%d-%d'%(today.year-1,today.year)
        if month_of >= 4:
            date_of = '%d-%d'%(today.year,today.year+1)
        search_condition = [('name', '=', date_of)]
        search_ids = self.pool.get('account.fiscalyear').search(cr, uid, search_condition, context=context)
        similar_objs = self.pool.get('account.fiscalyear').browse(cr, uid, search_ids, context=context)
        if similar_objs:
            return similar_objs[0].id
        return False
    
    def _get_invoice_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.invoice.line').browse(cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()

    def _get_invoice_tax(self, cr, uid, ids, context=None):
        result = {}
        for tax in self.pool.get('account.invoice.tax').browse(cr, uid, ids, context=context):
            result[tax.invoice_id.id] = True
        return result.keys()
    
    def on_change_wakf_regno_to_name(self, cr, uid, ids, reg_no, context=None):
        values = {}
        if reg_no:
            id_res_partner=self.pool.get('res.partner')
            search_condition = [('wakf_reg_no', '=', reg_no)]
            search_ids = id_res_partner.search(cr, uid, search_condition, context=context)
            if search_ids:
                similar_objs = id_res_partner.browse(cr, uid, search_ids, context=context)
                partner_id = id_res_partner.browse(cr, uid, search_ids, context=context)[0].id
                values={'partner_id':partner_id,
                        }
                return {'value' :values}
        return False
    def on_change_wakf_acc_year_to_name(self, cr, uid, ids, reg_no,acc_year, context=None):
        values = {}
        date_from = False
        date_to = False
        total_income = False
        total_expense = False
        final_list = False
        invoice_lines1 = False
        invoice_lines2 = False
        search_ids = False
        output = False
        result = False
        if reg_no:
            id_res_partner=self.pool.get('res.partner')
            search_condition = [('wakf_reg_no', '=', reg_no)]
            search_ids = id_res_partner.search(cr, uid, search_condition, context=context)
            similar_objs = id_res_partner.browse(cr, uid, search_ids, context=context)
            if similar_objs:
                partner_id = id_res_partner.browse(cr, uid, search_ids, context=context)[0].id
                
        if partner_id:
            product_key = self.pool.get('assessment.window').search(cr, uid, [('wakf_id','=',partner_id)])
            product_open = self.pool.get('assessment.window.line1').search(cr, uid, [('assess_menu_id1','=',product_key)])
       
            ###########################################################################################
            invoice_lines1 = []
            if product_open:
                search_condition = [('acc_year','=',acc_year),('wakf_id', '=', partner_id)]
                search_ids = self.pool.get('assessment.window').search(cr, uid, search_condition)
                if search_ids:
                    id_first = self.pool.get('assessment.window').browse(cr, uid, search_ids)[0]
                    date_from = id_first.date_from
                    date_to = id_first.date_to
                    acc_year = id_first.acc_year
                    total_income = id_first.total_income
                    total_expense = id_first.total_expense
                else:
                    date_from = False
                    date_to = False
                    acc_year = False
                    total_income = False
                    total_expense = False
                    invoice_lines1.append((2,1))
                    return {'warning': {
                    'title': _('Warning!'),
                    'message':  _('No Records found for this wakf on specified Assessment Year. \n Re-Check records on -Assessment Window-'),                 
                    },'value':{'date_from':False,'date_to':False,'acc_year':False,'total_income':False,'total_expense':False,'invoice_line':invoice_lines1}}
            else:
                invoice_lines1.append((2,1))
                return {'warning': {
                    'title': _('Warning!'),
                    'message':  _('No Records found for this wakf on specified Assessment Year. \n Re-Check records on -Assessment Window-'),
                    },'value':{'date_from':False,'date_to':False,'acc_year':False,'total_income':False,'total_expense':False,'invoice_line':invoice_lines1}}
            if product_open:  
                product_ids1 = self.pool.get('assessment.window.line1').search(cr, uid, [('assess_menu_id1','=',search_ids)])
                for p1 in self.pool.get('assessment.window.line1').browse(cr, uid, product_ids1):
                    if(p1.statement_a.percentage_income != 0): # Deductable % more than zero
                        if(p1.statement_a.percentage_income != 100): # Deductable not equal to 100%
                            percentage_of_income = p1.statement_a.percentage_income
                            unit_price_entered_income = p1.amount
                            quantity_entered_income = p1.quantity
                            total_income = unit_price_entered_income*quantity_entered_income
                            percentage_of_income = 100-percentage_of_income
                            total_income_cal = total_income*percentage_of_income/100
                            invoice_lines1.append((0,0,{'product_id':p1.statement_a.id,'name':p1.description,'quantity':1,'price_subtotal':0,'price_unit':total_income_cal,'new_amount':total_income_cal}))   
                        else: # deductable is 100%
                            False
                    else: # Deductable is  0%
                        invoice_lines1.append((0,0,{'product_id':p1.statement_a.id,'name':p1.description,'quantity':p1.quantity,'price_subtotal':0,'price_unit':p1.unit_cost,'new_amount':p1.unit_cost}))
                        
                #res1['value']['invoice_line']=invoice_lines
                #return res1
                
                invoice_lines2 = []
                product_ids2 = self.pool.get('assessment.window.line2').search(cr, uid, [('assess_menu_id2','=',search_ids)])
                for p1 in self.pool.get('assessment.window.line2').browse(cr, uid, product_ids2):
                    if(p1.statement_a.percentage_expense != 0): #  IF Property having a reduction on assessment amount
                        percentage_of_expense = p1.statement_a.percentage_expense
                        if(p1.statement_a.deductable == True and p1.statement_a.related_id.id != False): # If it is Deductable and related with other property
                            product_ids1 = self.pool.get('assessment.window.line1').search(cr, uid, [('assess_menu_id1','=',search_ids)])
                            for entry in self.pool.get('assessment.window.line1').browse(cr, uid, product_ids1):# if expense related to income in order
                                if entry.statement_a.id == p1.statement_a.related_id.id:
                                    variable = True  #checking same variable exist in income line
                                    unit_price_entered = entry.amount
                                    quantity_entered = entry.quantity
                                    total_expense = unit_price_entered*quantity_entered
                                    maximum_exp_allowed = total_expense*percentage_of_expense/100
                                #else:
                                    #variable = False #If not present
                            if variable==True:
                                actual_entered_exp = p1.amount
                                actual_entered_exp_qty = p1.quantity
                                total_exp_entered = actual_entered_exp * actual_entered_exp_qty
                                if total_exp_entered > maximum_exp_allowed: # if write more than allowed expense==Wrong
                                    invoice_lines2.append((0,0,{'product_id':p1.statement_a.id,'name':p1.description,'quantity':1,'price_subtotal':0,'price_unit':-(maximum_exp_allowed),'new_amount':maximum_exp_allowed}))   
                                #else:
                                    #False
                                if total_exp_entered <= maximum_exp_allowed: # if write less than or equal to allowed expense =Right
                                    invoice_lines2.append((0,0,{'product_id':p1.statement_a.id,'name':p1.description,'quantity':1,'price_subtotal':0,'price_unit':-(p1.amount),'new_amount':-(p1.amount)}))   
                                #else:
                                    #False
                            #else:# if no income matches with this expense
                                #False                      
                        else:#have deduction but no relation
                            False
                            #invoice_lines2.append((0,0,{'product_id':p1.statement_a.id,'name':p1.description,'quantity':p1.quantity,'price_subtotal':p1.amount,'price_unit':-(p1.unit_cost)}))   
                        if(p1.statement_a.deductable == False and p1.statement_a.percentage_expense != 0): # If it is Deductable and related with other property
                            amount = p1.amount * percentage_of_expense / 100
                            invoice_lines2.append((0,0,{'product_id':p1.statement_a.id,'name':p1.description,'quantity':1,'price_subtotal':0,'price_unit':-(amount),'new_amount':-(amount)}))   
                    else:
                        False
                final_list = invoice_lines1 + invoice_lines2
            else:
                invoice_lines = False
                return {'warning': {
                    'title': _('Warning!'),
                    'message':  _('Please add properties for assessment'),                 
                    }
                }
            
            ###########################################################################################
            
        result = {'value': {
           
            #'registration_no':p.wakf_reg_no,
            'date_from':date_from or False,
            'date_to':date_to or False,
            #'assess_year_saleorder':acc_year,
            'total_income_saleorder':total_income or False,
            'total_expense_saleorder':total_expense or False,
            'partner_id':partner_id,
            'invoice_line':final_list,
            
           
            }
        }

        return result
    
    #def on_change_state(self, cr, uid, ids, state,reg_no,acc_year, context=None):
     #   browse_ids = []
     #   #if state == 'paid':
     #   search_condition = [('acc_year','=',acc_year.id)]
     #   search_ids = self.pool.get('assessment.window').search(cr,uid,[])
     #   browse_ids = [rec.id for rec in self.pool.get('assessment.window').browse(cr,uid,search_ids)]
     #   self.pool.get('assessment.window').write(cr,uid,1,{'state':'completed'},context=None)
     #   return True
     
    def confirm_paid(self, cr, uid, ids, context=None):
        pension_list = []
        if context is None:
            context = {}
        for rec in self.browse(cr,uid,ids):
            reg_no = rec.registration_no
            acc_year = rec.assess_year_saleorder.id
            assess_year = rec.account_year_saleorder.id
            is_sws = rec.is_sws
            is_assessment = rec.is_assessment
            type = rec.type
            application_no = rec.appli_no
            partner_id = rec.partner_id.id
            assessment_type = rec.assessment_type
            ###################### SWS ################
            head_name = rec.head.name
            head = rec.head.id
            for_month = rec.for_month
            year = rec.year
            amount = rec.amount
            key = rec.key
            ###########################################
        if is_assessment and type == 'out_invoice' and assessment_type == 'assessment':  ### Direct Assessments
            search_ids = self.pool.get('assessment.window').search(cr,uid,[('name','=',reg_no),('acc_year','=',acc_year),('assess_year','=',assess_year)])
            self.pool.get('assessment.window').write(cr,uid,search_ids,{'state':'completed'},context=None)    
        if is_assessment and type == 'out_invoice' and assessment_type == 'bj':  ### BJ Assessments
            search_ids = self.pool.get('assessment.window').search(cr,uid,[('name','=',reg_no),('acc_year','=',acc_year),('assess_year','=',assess_year)])
            self.pool.get('assessment.window').write(cr,uid,search_ids,{'state':'completed'},context=None)
            search_ids = self.pool.get('bj.assessment.window').search(cr,uid,[('reg_no','=',reg_no),('account_year','=',acc_year),('assessment_year','=',assess_year)])
            self.pool.get('bj.assessment.window').write(cr,uid,search_ids,{'state':'completed'},context=None)
        if is_assessment and type == 'out_invoice' and assessment_type == 'rr':  ### RR Assessments
            #search_ids = self.pool.get('assessment.window').search(cr,uid,[('name','=',reg_no),('acc_year','=',acc_year),('assess_year','=',assess_year)])
            #self.pool.get('assessment.window').write(cr,uid,search_ids,{'state':'completed'},context=None)
            search_ids = self.pool.get('revenue.recovery').search(cr,uid,[('reg_no','=',reg_no),('assess_year','=',assess_year)])
            self.pool.get('revenue.recovery').write(cr,uid,search_ids,{'state':'execute'},context=None)
        if is_sws and head_name == "Education Loan":   #### Education Loan
            stat_assess = 'revolving'
            search_ids = self.pool.get('res.partner').search(cr,uid,[('appli_no','=',application_no)])
            if search_ids:
                browse_ids = self.pool.get('res.partner').browse(cr,uid,search_ids)
                amount_sanctioned = browse_ids.amount_sanction 
            self.pool.get('res.partner').write(cr,uid,search_ids,{'state1':'paid'},context=None)
        if is_sws and type == 'in_invoice' and head_name != "Pension":   ### Other SWS non re-fundable
            search_ids = self.pool.get('res.partner').search(cr,uid,[('appli_no','=',application_no)])
            self.pool.get('res.partner').write(cr,uid,search_ids,{'state1':'finished'},context=None)
        if is_sws and type == 'in_invoice' and head_name == "Pension":   ### Pension SWS non re-fundable
            search_ids = self.pool.get('res.partner').search(cr,uid,[('appli_no','=',application_no),('head','=',head),('state1','!=','finished')])
            status = 'pending'
            unlink_list = []
            unlink_list.append((2,1))
            if not search_ids:
                raise osv.except_osv(_('Warning!'), _('Undefined or closed transaction on Pension'))
            browse_ids = self.pool.get('res.partner').browse(cr,uid,search_ids)
            for line in browse_ids:
                for line2 in line.history_transaction:
                    month_test = line2.for_month
                    year_test = line2.year
                    amount1 = line2.amount
                    if month_test == for_month and year_test == year and amount1 == amount:
                        status = 'paid'
                    pension_list.append((0,0,{'for_month':month_test,'year':year_test,'amount':amount1,'status':status}))
                    status = 'pending'
                self.pool.get('res.partner').write(cr,uid,search_ids,{'history_transaction':False})
                self.pool.get('res.partner').write(cr,uid,search_ids,{'history_transaction':pension_list})
            self.pool.get('res.partner').write(cr,uid,search_ids,{'state1':'revolving'})

        self.write(cr, uid, ids, {'state':'paid'}, context=context)
        return True
        
    _columns = {
            #'partner_id': fields.many2one('res.partner', 'Partner', change_default=True, readonly=True, required=True, states={'draft':[('readonly',False)]}, track_visibility='always'),
            'registration_no':fields.integer('Registration Number', size=16, required=False),
            'fiscal_position': fields.many2one('account.fiscal.position', 'Fiscal Position', readonly=True, states={'draft':[('readonly',False)]}),            
            'assessment_type':fields.selection((('assessment','Assessment'), ('BJ','BJ-Assessment')),'Assessment Type',required=True),   
            'date_from':fields.date('From date',required=False),
            'date_to':fields.date('To date',required=False),
            'total_income_saleorder':fields.char('Total Income', size=16, required=False),
            'total_expense_saleorder':fields.char('Total Expense', size=16, required=False),
            'cash_hand_saleorder':fields.char('Cash in Hand', size=16, required=False),
            'assessment_type':fields.selection((('assessment','Direct Assessment'), ('bj','BJ Assessment'),('rr','Revenue Recovery')),'Assessment Type',required=False), 
            #'assess_year_saleorder':fields.char('Assessment Year', size=16, required=True),
            'assess_year_saleorder':fields.many2one('account.fiscalyear','Account Year',ondelete='set null'),
            'account_year_saleorder':fields.many2one('account.fiscalyear','Assessment Year',ondelete='set null'),
            'cash_bank_saleorder':fields.char('Cash in Bank', size=16, required=False),
            'revised':fields.boolean('Revised',size=16),
            'order_no':fields.char('Order details',size=16),
            'order_date':fields.date('Order date'), 
            'user_id': fields.many2one('res.users', 'Wakf Officer', readonly=True, track_visibility='onchange', states={'draft':[('readonly',False)]}), 
            #'net_amount':fields.float('Net Amount', required=False),
            'net_amount': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Net Amount', track_visibility='always',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            },
            multi='all'),

            'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Contribution', track_visibility='always',invisible=True,
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            },
            multi='all'),
            'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Final amount',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            },
            multi='all'), 
            
            'is_assessment':fields.boolean('Assessment'),
            'is_sws':fields.boolean('SWS'),  
            'appli_no':fields.char('Application Number',readonly=True), 
            ###############################  SWS  #####################
            'head': fields.many2one('product.category','Head',ondelete='set null'),
            'for_month':fields.char('For Month',size=16),
            'year':fields.char('Year',size=16),
            'amount':fields.float('Amount'),
            'key':fields.char('Key',size=16),
            ########################################################### 
                }
            
    _defaults ={
                'date_invoice': lambda *a: time.strftime(DEFAULT_SERVER_DATE_FORMAT),
                'account_year_saleorder':_deflt_ass_year,
                'assessment_type':'assessment',
                
                }
    
invoice_inherit()

##########################################################################################################################
##########################################################################################################################

class assessment_income_line(osv.osv):
    
    _name = 'assessment.window.line1'
    def get_total_multiplication(self, cr, uid, ids, fields, arg, context):
        multi={}
        for record in self.browse(cr, uid, ids):
            multi[record.id]= record.quantity * record.unit_cost
        return multi
    
    def on_change_property_percentage(self, cr, uid, ids,product,amount, context=None):
        obj_product = self.pool.get('product.product')
        values = {}
        if product and amount:
            search_product = obj_product.search(cr,uid,[('id','=',product)])
            if search_product:
                browse_income = obj_product.browse(cr,uid,search_product)[0]
                income_percentage = browse_income.percentage_income
                exmpt_amount = amount * income_percentage / 100
                amount_total = amount - exmpt_amount
                values = {'exmpt_percentage':income_percentage,
                          'exmpt_amount':exmpt_amount,
                          'amount_total':amount_total,
                          'exmpt_percentage_copy':income_percentage,
                          'exmpt_amount_copy':exmpt_amount,
                          'amount_total_copy':amount_total
                          }
                return {'value':values}
        return False
    _columns = {
                'statement_a':fields.many2one('product.product','Income',domain=[('income', '=', True),('sale_ok', '=', True)],ondelete='set null',required=True),
                'unit_cost':fields.float('Amount',size=16),
                'assess_menu_id1':fields.many2one('assessment.window','Income',ondelete='set null'),
                'exmpt_percentage':fields.float('Exempted(%)',states={'unsaved':[('readonly',True)]},readonly=False),
                'exmpt_amount':fields.float('Amount Exempted',states={'unsaved':[('readonly',True)]},readonly=False),
                'amount_total':fields.float('Sub Total',states={'unsaved':[('readonly',True)]},readonly=False),

                
                'state': fields.selection([
                    ('unsaved', 'Submitted'),
                    ('saved', 'Notice Send'),
                    ],'status', readonly=False),
                }
    _defaults = {
                 'state':'unsaved'
        
    }
        
assessment_income_line()

class assessment_income_line_copy(osv.osv):
    
    _name = 'assessment.window.line1.copy'
    _columns = {
                'statement_a':fields.many2one('product.product','Income',domain=[('income', '=', True),('sale_ok', '=', True)],ondelete='set null',required=True),
                'unit_cost':fields.float('Amount',size=16),
                'assess_menu_id1_copy':fields.many2one('assessment.window','Incomecopy',ondelete='set null'),
                'exmpt_percentage':fields.float('Exempted(%)',readonly=False),
                'exmpt_amount':fields.float('Amount Exempted',readonly=False),
                'amount_total':fields.float('Sub Total',readonly=False),
    
        }
assessment_income_line_copy()

class assessment_expense_line(osv.osv):
    
    _name = 'assessment.window.line2'
    def get_total_multiplication(self, cr, uid, ids, fields, arg, context):
        multi={}
        for record in self.browse(cr, uid, ids):
            multi[record.id]= record.quantity * record.unit_cost
        return multi
    
    def on_change_property_percentage(self, cr, uid, ids,product,amount, context=None):
        obj_product = self.pool.get('product.product')
        values = {}
        related = False
        if product and amount:
            search_product = obj_product.search(cr,uid,[('id','=',product)])
            if search_product:
                browse_income = obj_product.browse(cr,uid,search_product)[0]
                related = browse_income.deductable
                expense_percentage = browse_income.percentage_expense
                exmpt_amount = amount * expense_percentage / 100
                amount_total = amount - exmpt_amount
                if not related:
                    values = {'ded_percentage':expense_percentage,
                              'ded_amount':exmpt_amount,
                              'amount_total':amount_total,
                              'related':False,
                              }
                if related:
                    values = {'ded_percentage':expense_percentage,
                              'ded_amount':0,
                              'amount_total':0,
                              'related':True,
                              }
                return {'value':values}
        return False
    _columns = {
                'statement_b':fields.many2one('product.product','Expense',domain=[('expense', '=', True),('sale_ok', '=', True)],ondelete='set null',required=True),
                'unit_cost':fields.float('Amount',size=16),
                'assess_menu_id2':fields.many2one('assessment.window','Expense',ondelete='set null'),
                'ded_percentage':fields.float('Deducted(%)',states={'unsaved':[('readonly',True)]},readonly=False),
                'ded_amount':fields.float('Amount Deducted',states={'unsaved':[('readonly',True)]},readonly=False),
                'amount_total':fields.float('Sub Total',states={'unsaved':[('readonly',True)]},readonly=False),
                'related':fields.boolean('Related',states={'unsaved':[('readonly',True)]},readonly=False),
                'state': fields.selection([
                    ('unsaved', 'Submitted'),
                    ('saved', 'Notice Send'),
                    ],'status', readonly=False),
                }
    _defaults = {
                'state':'unsaved'
    }
        
assessment_expense_line()


class assessment_expense_line_copy(osv.osv):
    
    _name = 'assessment.window.line2.copy'
   
    _columns = {
                'statement_b':fields.many2one('product.product','Expense',domain=[('expense', '=', True),('sale_ok', '=', True)],ondelete='set null',required=True),
                'unit_cost':fields.float('Amount',size=16),
                'assess_menu_id2_copy':fields.many2one('assessment.window','ExpenseCopy',ondelete='set null'),
                'ded_percentage':fields.float('Deducted(%)'),
                'ded_amount':fields.float('Amount Deducted'),
                'amount_total':fields.float('Sub Total'),
                'related':fields.boolean('Related'),
                }
        
assessment_expense_line_copy()


class assessment_window(osv.osv):
    
    _name = 'assessment.window'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    
    def _total_amount_wakf(self, cr, uid, ids, field_name, arg, context=None):
        val1 = 0
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
            'total_income' : 0,
            }
            state = order.state
            if state not in ['submitted','sent_notice','invoiced','showcause','RR','appeal','re-assess','completed']: 
                for line in order.assess_line_id1:
                    val1 += line.amount_total
            if state in ['submitted','sent_notice','invoiced','showcause','RR','appeal','re-assess','completed']: 
                for line in order.assess_line_id1_copy:
                    val1 += line.amount_total
            res[order.id]['total_income']=val1          
        return res
    def _total_amount_wakf1(self, cr, uid, ids, field_name, arg, context=None):
        val1 = 0
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
            'amount_total1' : 0,
            }
            state = order.state
            if state not in ['submitted','sent_notice','invoiced','showcause','RR','appeal','re-assess','completed']: 
                for line in order.assess_line_id1:
                    val1 += line.amount_total
            if state in ['submitted','sent_notice','invoiced','showcause','RR','appeal','re-assess','completed']: 
                for line in order.assess_line_id1_copy:
                    val1 += line.amount_total
            res[order.id]['amount_total1']=val1          
        return res
    def _total_amount_wakf2(self, cr, uid, ids, field_name, arg, context=None):
        val1 = 0
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
            'total_expense' : 0,
            }
            state = order.state
            if state not in ['submitted','sent_notice','invoiced','showcause','RR','appeal','re-assess','completed']: 
                for line in order.assess_line_id2:
                    val1 += line.amount_total
            if state in ['submitted','sent_notice','invoiced','showcause','RR','appeal','re-assess','completed']: 
                for line in order.assess_line_id2_copy:
                    val1 += line.amount_total
            res[order.id]['total_expense']=val1          
        return res
    def _total_amount_wakf3(self, cr, uid, ids, field_name, arg, context=None):
        val1 = 0
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
            'amount_total2' : 0,
            }
            state = order.state
            if state not in ['submitted','sent_notice','invoiced','showcause','RR','appeal','re-assess','completed']: 
                for line in order.assess_line_id2:
                    val1 += line.amount_total
            if state in ['submitted','sent_notice','invoiced','showcause','RR','appeal','re-assess','completed']: 
                for line in order.assess_line_id2_copy:
                    val1 += line.amount_total
            res[order.id]['amount_total2']=val1          
        return res
    def get_total(self, cr, uid, ids, fields, arg, context):
        difference={}
        for record in self.browse(cr, uid, ids):
            difference[record.id]= record.total_income - record.total_expense
        return difference
    
    def on_change_acc_year_to_munbaki(self, cr, uid, ids, reg_no, acc_year, context=None):
        values = {}
        id_self = self.pool.get('assessment.window')
        if reg_no and acc_year:
            condition = [('id','=',acc_year)]
            search_fiscal = self.pool.get('account.fiscalyear').search(cr,uid,condition)
            browse_fiscal = self.pool.get('account.fiscalyear').browse(cr,uid,search_fiscal)[0]
            acc_year = browse_fiscal.name
            year_left = int(acc_year[:4])
            year_previous = '%d-%d'%(year_left-1,year_left)
            search_fiscal = self.pool.get('account.fiscalyear').search(cr,uid,[('name','=',year_previous)])
            if not search_fiscal:
                return {'value':{
                            'line_1': 0,
                            'line_2': 0,
                            'line_3': 0,
                    }}
                raise osv.except_osv(_('Warning!'), _('Please set %s fiscal year')%(year_previous))
            browse_fiscal = self.pool.get('account.fiscalyear').browse(cr,uid,search_fiscal)[0]
            previous_year_id = browse_fiscal.id
            condition = [('acc_year','=',previous_year_id),('name', '=', reg_no),('state','in', ['submitted','sent_notice','invoiced','showcause','RR','appeal','re-assess','completed'])]
            search_acc = id_self.search(cr,uid,condition,context=context)
            if search_acc:    
                ids_acc = id_self.browse(cr,uid,search_acc)[0]
                kaivasam = ids_acc.line_1
                bank = ids_acc.line_2
                dhanyam = ids_acc.line_3
                return {'value':{
                            'line_1': kaivasam,
                            'line_2': bank,
                            'line_3': dhanyam,
               
                    }}
            else:
                raise osv.except_osv(_('Warning!'), _('%s year datas not received yet')%(year_previous))
                return {'value':{
                            'line_1': 0,
                            'line_2': 0,
                            'line_3': 0,
                              }}
                
        return {'value' : values}
    def button_calculate(self,cr,uid,ids,fields,arg,context=None):
        unit_cost_income = 0
        unit_cost_expense = 0
        exempted_income = 0
        ded_income = 0
        total_income = 0
        total_expense = 0
        net = 0
        net1 = 0
        contri = 0
        dicti = {}
        for rec in self.browse(cr,uid,ids,context=context):
            dicti[rec.id] = {'exempted':0.0,
                             'deducted':0.0,
                             'total_income_final':0.0,
                             'total_expense_final':0.0,
                             'net_income':0.0,
                             'contribution_amount':0.0,
                             'munbaki':0.0
                             }
            kaivasam = rec.line_1
            bank = rec.line_2
            dhanyam = rec.line_3
            munbaki = kaivasam + bank + dhanyam
            state = rec.state
            if state not in ['submitted','sent_notice','invoiced','showcause','RR','appeal','re-assess','completed']:     
                for line in rec.assess_line_id1:    ##################  line of income ######################
                    unit_cost_income = unit_cost_income +line.unit_cost
                    exempted_income = exempted_income + line.exmpt_amount
                total_income = unit_cost_income
                for line in rec.assess_line_id2:    ##################  line of Expense ######################
                    unit_cost_expense = unit_cost_expense +line.unit_cost
                    ded_income = ded_income + line.ded_amount
            if state in ['submitted','sent_notice','invoiced','showcause','RR','appeal','re-assess','completed']:     
                for line in rec.assess_line_id1_copy:    ##################  line of income ######################
                    unit_cost_income = unit_cost_income +line.unit_cost
                    exempted_income = exempted_income + line.exmpt_amount
                total_income = unit_cost_income
                for line in rec.assess_line_id2_copy:    ##################  line of Expense ######################
                    unit_cost_expense = unit_cost_expense +line.unit_cost
                    ded_income = ded_income + line.ded_amount
            total_expense = unit_cost_expense - ded_income
            net1 = total_income - (ded_income + munbaki + exempted_income)
            if net1 >= 0:
                net = net1
                contri = net * 7 / 100
            dicti[rec.id]['grand_income'] = total_income or False
            dicti[rec.id]['exempted'] = exempted_income or False
            dicti[rec.id]['deducted'] = ded_income or False
            dicti[rec.id]['total_income_final'] = total_income or False
            dicti[rec.id]['total_expense_final'] = total_expense or False
            dicti[rec.id]['net_income'] = net or False
            dicti[rec.id]['contribution_amount'] = contri or False
            dicti[rec.id]['munbaki'] = munbaki or False
        return dicti
    
    def final_calculate1(self, cr, uid, ids, fields, arg, context):
        difference={}
        for record in self.browse(cr, uid, ids):
            difference[record.id]= record.total_income - record.exempted
        return difference
    
    def final_calculate2(self, cr, uid, ids, fields, arg, context):
        difference={}
        for record in self.browse(cr, uid, ids):
            difference[record.id]= record.total_expense - record.deducted
        return difference
    
    def _deflt_ass_year(self, cr, uid, ids, context=None):
        res ={}
        today = date.today()
        month_of = today.month
        if month_of <= 3:
            date_of = '%d-%d'%(today.year-1,today.year)
        if month_of >= 4:
            date_of = '%d-%d'%(today.year,today.year+1)
        search_condition = [('name', '=', date_of)]
        search_ids = self.pool.get('account.fiscalyear').search(cr, uid, search_condition, context=context)
        similar_objs = self.pool.get('account.fiscalyear').browse(cr, uid, search_ids, context=context)
        if similar_objs:
            return similar_objs[0].id
        return False
    
    def on_change_wakf_regno_to_name_new_assess(self, cr, uid, ids, reg_no, acc_year, context=None):
        values = {}
        values1 = {}
        id_res_partner = self.pool.get('res.partner')
        id_self = self.pool.get('assessment.window')
        if reg_no:
            search_condition = [('wakf_reg_no', '=', reg_no)]
            search_ids = id_res_partner.search(cr, uid, search_condition, context=context)
            similar_objs = id_res_partner.browse(cr, uid, search_ids, context=context)
            if similar_objs:
                output = id_res_partner.browse(cr, uid, search_ids, context=context)[0].id
                district = id_res_partner.browse(cr, uid, search_ids, context=context)[0].district_id.id
                values = {
                            'wakf_id': output,
                            'district':district
               
                    }
            else:
                values ={
                            'wakf_id': False,
                            'district':False
                              }
        if reg_no and acc_year:
            condition = [('id','=',acc_year)]
            search_fiscal = self.pool.get('account.fiscalyear').search(cr,uid,condition)
            browse_fiscal = self.pool.get('account.fiscalyear').browse(cr,uid,search_fiscal)[0]
            acc_year = browse_fiscal.name
            year_left = int(acc_year[:4])
            year_previous = '%d-%d'%(year_left-1,year_left)
            search_fiscal = self.pool.get('account.fiscalyear').search(cr,uid,[('name','=',year_previous)])
            if not search_fiscal:
                return {'value':{
                            'line_1': 0,
                            'line_2': 0,
                            'line_3': 0,
                    }}
                raise osv.except_osv(_('Warning!'), _('Please set %s fiscal year')%(year_previous))
            browse_fiscal = self.pool.get('account.fiscalyear').browse(cr,uid,search_fiscal)[0]
            previous_year_id = browse_fiscal.id
            condition = [('acc_year','=',previous_year_id),('name', '=', reg_no),('state','in', ['submitted','sent_notice','invoiced','showcause','RR','appeal','re-assess','completed'])]
            search_acc = id_self.search(cr,uid,condition,context=context)
            if search_acc:    
                ids_acc = id_self.browse(cr,uid,search_acc)[0]
                kaivasam = ids_acc.line_1
                bank = ids_acc.line_2
                dhanyam = ids_acc.line_3
                return {'value':{
                            'line_1': kaivasam,
                            'line_2': bank,
                            'line_3': dhanyam,
               
                    }}
            else:
                
                return {'value':{
                            'line_1': 0,
                            'line_2': 0,
                            'line_3': 0,
                              }}
                raise osv.except_osv(_('Warning!'), _('%s year datas not received yet')%(year_previous))
                
        return {'value' : dict(values.items() + values1.items())}
    def action_submit(self, cr, uid, ids, context=None):
        follow_list = []
        values_income = []
        values_expense = []
        dicto = {}
        related = False
        obj_product = self.pool.get('product.product')
        for rec in self.browse(cr, uid, ids, context=context):
            for line in rec.assess_line_id1:    ##################  line of income ######################
                product = line.statement_a.id
                amount = line.unit_cost
                if product and amount:
                    search_product = obj_product.search(cr,uid,[('id','=',product)])
                    if search_product:
                        browse_income = obj_product.browse(cr,uid,search_product)[0] 
                        income_percentage = browse_income.percentage_income
                        exmpt_amount = amount * income_percentage / 100
                        amount_total = amount - exmpt_amount
                        values_income.append((0,0,{'statement_a':product,'unit_cost':amount,'exmpt_percentage':income_percentage,'exmpt_amount':exmpt_amount,'amount_total':amount_total}))   
                ##############################################################
            for line_exp in rec.assess_line_id2:    ##################  line of expense ######################
                product = line_exp.statement_b.id
                amount = line_exp.unit_cost
                percentage_exp = line_exp.ded_percentage
                expense_percentage = percentage_exp
                if product and amount:
                    search_product = obj_product.search(cr,uid,[('id','=',product)])
                    if search_product:
                        browse_income = obj_product.browse(cr,uid,search_product)[0] 
                        if browse_income.deductable:
                            related_id = browse_income.related_id.id   # Fetching related id from master table
                            for line in rec.assess_line_id1:
                                if line.statement_a.id == related_id:   ## IF matching records on income side
                                    related_income = line.unit_cost * percentage_exp / 100
                                    related_expense = amount
                                    if related_income >= related_expense:
                                        exmpt_amount = related_expense
                                        amount_total = related_expense
                                    else:
                                        exmpt_amount = related_income
                                        amount_total = related_expense
                                    related = True
                        else:
                            expense_percentage = browse_income.percentage_expense
                            deducted_amount = amount * expense_percentage / 100
                            amount_total = amount - deducted_amount
                            exmpt_amount = deducted_amount
                        values_expense.append((0,0,{'related':related,'statement_b':product,'unit_cost':amount,'ded_percentage':expense_percentage,'ded_amount':exmpt_amount,'amount_total':amount_total}))   
                        related = False
            dicto = {'name':"Submitted",'who':uid,'when':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
            follow_list.append((0,0,dicto))
            #self.write(cr, uid, ids, {'assess_line_id1':False})
        self.write(cr, uid, ids, {'state':'submitted','follow_up_id':follow_list,'assess_line_id1_copy':values_income,'assess_line_id2_copy':values_expense})
        return True
    
    #def action_sent_notice(self, cr, uid, ids, context=None):
    #    follow_list = []
    #       dicto = {'name':"Notice Send",'who':uid,'when':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
    #        follow_list.append((0,0,dicto))
    #        self.write(cr, uid, ids, {'state':'sent_notice','follow_up_id':follow_list})
    #    return True
    
    def action_sent_notice(self, cr, uid, ids, context=None):
        invoice_ids = []
        follow_list = []
        dicto = {}
        for rec in self.browse(cr, uid, ids, context=context):
            dicto = {'name':"Invoiced(Draft)",'who':uid,'when':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
            follow_list.append((0,0,dicto))
            price_unit_income = rec.net_income
            new_amount_income = rec.net_income
            price_unit_expense = rec.total_expense_final
            new_amount_expense = rec.total_expense_final
            output = rec.wakf_id.id
            acc_year = rec.acc_year.id
            ass_year = rec.assess_year.id
            reg_no = rec.name
            search_ids = self.pool.get('product.product').search(cr,uid,[('name','=',"INCOME")])
            if not search_ids:
                raise osv.except_osv(_('Warning!'), _('Please set "INCOME" as a Property'))
            income_id = self.pool.get('product.product').browse(cr,uid,search_ids)[0].id
            search_ids = self.pool.get('product.product').search(cr,uid,[('name','=',"EXPENSE")])
            if not search_ids:
                raise osv.except_osv(_('Warning!'), _('Please set "EXPENSE" as a Property'))
            expense_id = self.pool.get('product.product').browse(cr,uid,search_ids)[0].id
            ##############################################################################################################
            search_ids = self.pool.get('account.account').search(cr,uid,[('name','=',"Accounts Receivable")])
            if not search_ids:
                raise osv.except_osv(_('Warning!'), _('Please create an account "Accounts Receivable" first'))
            account_id = self.pool.get('account.account').browse(cr,uid,search_ids)[0].id
            
            search_ids = self.pool.get('account.journal').search(cr,uid,[('name','=',"Assessment Journal")])
            if not search_ids:
                raise osv.except_osv(_('Warning!'), _('Please create "Assessment Journal" First'))
            journal_id = self.pool.get('account.journal').browse(cr,uid,search_ids)[0].id
            invoice_ids.append((0,0,{'product_id':income_id,'name':" Net Income",'quantity':1,'price_unit':price_unit_income,'new_amount':new_amount_income,'sws':False}))   # sws =True, 7% calculation disabled
            #invoice_ids.append((0,0,{'product_id':expense_id,'name':"Income(Processed)",'quantity':1,'price_unit':-price_unit_expense,'new_amount':-new_amount_expense,'sws':True})) # sws =True, 7% calculation disabled
            id_create = self.pool.get('account.invoice').create(cr,uid,{'type':'out_invoice', 'journal_type': 'sale','assessment_type':'assessment','registration_no':reg_no,'assess_year_saleorder':acc_year,'account_year_saleorder':ass_year,'is_assessment':True,'appli_no':False,'account_id':account_id,'journal_id':journal_id,'partner_id':output,'invoice_line':invoice_ids,'total_income_saleorder':price_unit_income,'total_expense_saleorder':price_unit_expense})
        
        self.write(cr, uid, ids, {'state':'invoiced','follow_up_id':follow_list})
        return {
            'type': 'ir.actions.act_window',
            'name': "Invoice form",
            'view_type': 'form',
            'view_mode': 'form',
            'context': {'default_type':'out_invoice', 'type':'out_invoice', 'journal_type': 'sale'},
            'res_id':id_create,
            #'domain' : [('order_id','in',sale_ids)],
            'res_model': 'account.invoice',
            'target': 'new',
            'nodestroy': True,}
    
    def action_showcause(self, cr, uid, ids, context=None):
        follow_list = []
        dicto = {}  
        for rec in self.browse(cr, uid, ids, context=context):
            dicto = {'name':"Showcause Created",'who':uid,'when':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
            follow_list.append((0,0,dicto))
            sequence=self.pool.get('ir.sequence').get(cr, uid, 'SHOWCAUSE')
            reg_no = rec.name
            partner_id = rec.wakf_id.id
            acc_year = rec.acc_year.id
            ass_year = rec.assess_year.id
            notice_no = sequence
            amount = (rec.total_income_final - rec.total_expense_final)*7/100
            self.pool.get('show.cause').create(cr,uid,{'reg_no':reg_no,'partner_id':partner_id,'notice_no':notice_no,'amount':amount,'assessment_year':ass_year,'acc_year_from':acc_year,'acc_year_to':acc_year})
        self.write(cr, uid, ids, {'state':'showcause','showcause_notice_no':sequence,'showcause_tick':True,'follow_up_id':follow_list})
        return True
    
    def action_appeal(self, cr, uid, ids, context=None):
        follow_list = []
        dicto = {}
        for rec in self.browse(cr, uid, ids, context=context):
            dicto = {'name':"Appeal Received",'who':uid,'when':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
            follow_list.append((0,0,dicto))
            self.write(cr, uid, ids, {'state':'appeal','follow_up_id':follow_list})
        return True
    
    def action_RR(self, cr, uid, ids, context=None):
        follow_list = []
        dicto = {}
        for rec in self.browse(cr, uid, ids, context=context):
            dicto = {'name':"Send to RR",'who':uid,'when':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
            follow_list.append((0,0,dicto))
            reg_no = rec.name
            output = rec.wakf_id.id
            acc_year = rec.acc_year.id
            ass_year = rec.assess_year.id
            self.write(cr, uid, ids, {'state':'re-assess','follow_up_id':follow_list})
            search_invoice = self.pool.get('account.invoice').search(cr,uid,[('partner_id','=',output),('assess_year_saleorder','=',acc_year),('account_year_saleorder','=',ass_year),('is_assessment','=',True),('appli_no','=',False),('assessment_type','=','assessment'),('state','=','draft')])
            list_unlink = [ invoice.id for invoice in self.pool.get('account.invoice').browse(cr,uid,search_invoice)]
            self.pool.get('account.invoice').unlink(cr,uid,list_unlink,context=context)
            self.write(cr, uid, ids, {'state':'RR','follow_up_id':follow_list})
            ##########################################  RR Created  ##########################################
            id_create = self.pool.get('revenue.recovery').create(cr,uid,{'from_a':'assessment','reg_no':reg_no,'partner_id':output,'assess_year':ass_year})
       
        return {
            'type': 'ir.actions.act_window',
            'name': "Revenue Recovery form",
            'view_type': 'form',
            'view_mode': 'form',
            'context': context,
            'res_id':id_create,
            #'domain' : [('order_id','in',sale_ids)],
            'res_model': 'revenue.recovery',
            'target': 'new',
            'nodestroy': True,}
    
    def action_re_assess(self, cr, uid, ids, context=None):
        follow_list = []
        income_list = []
        expense_list = []
        dicto = {}
        for rec in self.browse(cr, uid, ids, context=context):
            dicto = {'name':"Re-assessment",'who':uid,'when':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
            follow_list.append((0,0,dicto))
            reg_no = rec.name
            output = rec.wakf_id.id
            acc_year = rec.acc_year.id
            ass_year = rec.assess_year.id
            district = rec.district.id
            taluk = rec.taluk.id
            village = rec.village.id
            assess_date = rec.date_from
            for income in rec.assess_line_id1:
                property = income.statement_a.id
                unit_cost = income.unit_cost
                percentage = income.exmpt_percentage
                exmpt_amount = income.exmpt_amount
                total = income.amount_total
                income_list.append((0,0,{'statement_a':property,'unit_cost':unit_cost,'exmpt_percentage':percentage,'exmpt_amount':exmpt_amount,'amount_total':total}))
            for expense in rec.assess_line_id2:
                property = expense.statement_b.id
                unit_cost = expense.unit_cost
                percentage = expense.ded_percentage
                exmpt_amount = expense.ded_amount
                total = expense.amount_total
                expense_list.append((0,0,{'statement_b':property,'unit_cost':unit_cost,'ded_percentage':percentage,'ded_amount':exmpt_amount,'amount_total':total}))
            #################################### unlinking ###############################
            self.write(cr, uid, ids, {'state':'re-assess','follow_up_id':follow_list})
            search_invoice = self.pool.get('account.invoice').search(cr,uid,[('partner_id','=',output),('assess_year_saleorder','=',acc_year),('account_year_saleorder','=',ass_year),('is_assessment','=',True),('appli_no','=',False),('assessment_type','=','assessment'),('state','=','draft')])
            list_unlink = [ invoice.id for invoice in self.pool.get('account.invoice').browse(cr,uid,search_invoice)]
            self.pool.get('account.invoice').unlink(cr,uid,list_unlink,context=context)
            ##############################################################################
            create_id = self.create(cr,uid,{'name':reg_no,'acc_year':acc_year,'wakf_id':output,'district':district,'taluk':taluk,'village':village,'date_from':assess_date,'assess_year':ass_year,'revised':True,'assess_line_id1':income_list,'assess_line_id2':expense_list})
            self.write(cr, uid, ids, {'state':'re-assess','follow_up_id':follow_list})
        return {
            'type': 'ir.actions.act_window',
            'name': "Re-assessment form",
            'view_type': 'form',
            'view_mode': 'form',
            'context': context,
            'res_id':create_id,
            #'domain' : [('order_id','in',sale_ids)],
            'res_model': 'assessment.window',
            'target': 'new',
            'nodestroy': True,}
    
    #def unlink(self, cr, uid, ids, context=None):
    #    if context is None:
    #        context = {}
    #    """Allows to delete assessment lines in other states"""
    #    for rec in self.browse(cr, uid, ids, context=context):
    #        if rec.state not in ['submitted']:
    #            raise osv.except_osv(_('Invalid Action!'), _('Cannot delete an Assessment Record which is in state \'%s\'.') %(rec.state,))
    #    return super(assessment_window, self).unlink(cr, uid, ids, context=context)
    
    def _get_schedule_ids_for_order(self, cr, uid, ids, context=None):
        for rec in self.browse(cr,uid,ids):
            if rec.paid == True:
                self = assessment_window.pool.get('assessment.window').create(cr,uid,{'name':"PAPA"})
    
    _columns = {
                'wakf_id':fields.many2one('res.partner','Wakf Name',ondelete='set null',required=False),
                'name':fields.integer('Registration No:',size=16,required=False),
                'district':fields.many2one('wakf.district','District',ondelete='set null',required=False),
                'taluk':fields.many2one('wakf.taluk','Village',ondelete='set null'),
                'village':fields.many2one('wakf.taluk','Taluk',ondelete='set null'),
                'date_from':fields.date('Assessment Date:',required=False),
                'date_to':fields.date('Assessment Date To:',required=False),
                'acc_year':fields.many2one('account.fiscalyear','Account Year',ondelete='set null'),
                #'acc_year':fields.char('Account Year',size=16,required=False),
                'assess_year':fields.many2one('account.fiscalyear','Assessment Year',size=16,required=False),
                'assess_line_id1':fields.one2many('assessment.window.line1','assess_menu_id1','Income'),
                'assess_line_id1_copy':fields.one2many('assessment.window.line1.copy','assess_menu_id1_copy','Income copy',states={'submitted':[('readonly',True)],'sent_notice':[('readonly',True)],'invoiced':[('readonly',True)],'showcause':[('readonly',True)],'RR':[('readonly',True)],'appeal':[('readonly',True)],'re-assess':[('readonly',True)]}),
                'assess_line_id2':fields.one2many('assessment.window.line2','assess_menu_id2','Expense'),
                'assess_line_id2_copy':fields.one2many('assessment.window.line2.copy','assess_menu_id2_copy','Expense copy',states={'submitted':[('readonly',True)],'sent_notice':[('readonly',True)],'invoiced':[('readonly',True)],'showcause':[('readonly',True)],'RR':[('readonly',True)],'appeal':[('readonly',True)],'re-assess':[('readonly',True)]}),
                'total_income':fields.function(_total_amount_wakf,multi='sums',string='Total Income',store=False),
                'total_expense':fields.function(_total_amount_wakf2,multi='sums2',string='Total Expense',store=False),
                'assess_amount':fields.function(get_total,string='Difference Amount',store=True,type='float',method=False),
                'amount_total1':fields.function(_total_amount_wakf1,multi='sums1',string='Subtotal',store=False),
                'amount_total2':fields.function(_total_amount_wakf3,multi='sums3',string='Subtotal',store=False),
                'description2':fields.text('Extra info',size=32),
                'line_1':fields.float('kaivasam'),
                'line_2':fields.float('bankil'),
                'line_3':fields.float('Dhanyam'),
                'user_id':fields.char('user id',size=16),
                'grand_income':fields.function(button_calculate,string='Total Income',type='float',multi='all',store=True,method=False),
                'exempted':fields.function(button_calculate,string='Exempted',type='float',multi='all',store=True,method=False),
                'deducted':fields.function(button_calculate,string='Deductable',type='float',multi='all',store=True,method=False),
                'munbaki':fields.function(button_calculate,string='Munbaki',type='float',multi='all',store=True,method=False),
                'total_income_final':fields.function(button_calculate,string='Total income',type='float',multi='all',store=True,method=False),
                'total_expense_final':fields.function(button_calculate,string='Total expense',type='float',multi='all',store=True,method=False),
                'net_income':fields.function(button_calculate,string='Net Income',type='float',multi='all',store=True,method=False),
                'contribution_amount':fields.function(button_calculate,string='Contribution',type='float',multi='all',store=True,method=False),
                #'showcause_notice_no':fields.char('Showcause Notice No',size=16),
                #'showcause_tick':fields.boolean('Showcause tick',size=16),
                'follow_up_id':fields.one2many('follow.up','follow_id','Follow Up'),
                'appeal_no':fields.char('Appeal or Case No',size=16),
                'appeal_details':fields.text('Judgement/Order Details',size=16),
                'appeal_date':fields.date('Judgement/Order Date',size=16),
                'revised':fields.boolean('Revised'),
                'state': fields.selection([
                    ('submitted', 'Submitted'),
                    ('sent_notice', 'Notice Send'),
                    ('invoiced', 'Invoiced'),            
                    ('showcause', 'Showcause send'),
                    ('RR', 'RR Issued'),
                    ('appeal', 'Appeal Received'),
                    ('re-assess', 'Re-Assessment'),
                    ('completed', 'Completed'),
                    ],'status', readonly=False),
                'company_id': fields.many2one('res.company', 'Company', required=False)
                }
    _defaults = {
                 'date_from': lambda *a: time.strftime(DEFAULT_SERVER_DATE_FORMAT),
                 'user_id': lambda obj, cr, uid, context: uid,
                 'assess_year': _deflt_ass_year,
                 'company_id': lambda self,cr,uid,ctx: self.pool['res.company']._company_default_get(cr,uid,object='assessment.window',context=ctx)
                }
assessment_window()
####################################################################################################################################
class invoice_line_inherit(osv.osv):
    
    _inherit = 'account.invoice.line'
    
    def _amount_line(self, cr, uid, ids, prop, unknow_none, unknow_dict):
        res = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        for line in self.browse(cr, uid, ids):
            price = line.price_unit * (1-(line.discount or 0.0)/100.0)
            taxes = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, price, line.quantity, product=line.product_id, partner=line.invoice_id.partner_id)
            res[line.id] = taxes['total']
            if line.invoice_id:
                cur = line.invoice_id.currency_id
                res[line.id] = cur_obj.round(cr, uid, cur, res[line.id]) 
        if line.sws == False:      
            res[line.id] = res[line.id]*7/100
        return res
    
    _columns = {
            
            'product_id': fields.many2one('product.product', 'Category',domain=[('sale_ok', '=', True)], ondelete='set null', select=True),             
            'price_subtotal': fields.function(_amount_line, string='Amount', type="float",digits_compute= dp.get_precision('Account'), store=True),
            'new_amount':fields.float('Final Amount',size=16),
            'sws':fields.boolean('SWS')
                }
    
invoice_line_inherit()

class follow_up(osv.osv):
    
    _name = 'follow.up'
    
    _columns = {
               'name':fields.char('Action',readonly=True),
               'who':fields.many2one('res.users','Who',readonly=True),
               'when':fields.char('When',readonly=True), 
               'follow_id':fields.many2one('assessment.window','FOLLOW UP'),
                
                
                }
follow_up()


class account_voucher_inherit(osv.osv):
    
    _inherit = 'account.voucher'
    
    def on_change_wakf_regno_to_name(self, cr, uid, ids, reg_no, context=None):
        values = {}
        if reg_no:
            id_res_partner=self.pool.get('res.partner')
            search_condition = [('wakf_reg_no', '=', reg_no)]
            search_ids = id_res_partner.search(cr, uid, search_condition, context=context)
            if search_ids:
                similar_objs = id_res_partner.browse(cr, uid, search_ids, context=context)
                partner_id = id_res_partner.browse(cr, uid, search_ids, context=context)[0].id
                values={'partner_id':partner_id,
                        }
                return {'value' :values}
        else:
            return {'value' :False}               
            raise osv.except_osv(_('Warning!'), _('%d is not a registered wakf')%reg_no)

    
    _columns = {
            'registration_no':fields.integer('Registration No')
                }
    

account_voucher_inherit()




