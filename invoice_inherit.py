from osv import osv
from osv import fields
from tools.translate import _
import addons.decimal_precision as dp
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from datetime import date
from datetime import datetime
import time
import os

class invoice_inherit(osv.osv):
    
    _inherit = 'account.invoice'
    
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
        return similar_objs[0].id
    
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
            similar_objs = id_res_partner.browse(cr, uid, search_ids, context=context)
            if similar_objs:
                partner_id = id_res_partner.browse(cr, uid, search_ids, context=context)[0].id
                values={'partner_id':partner_id,
                        'assess_year_saleorder':False
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
        if is_assessment and type == 'out_invoice':  ### Other Assessments
            search_ids = self.pool.get('assessment.window').search(cr,uid,[('name','=',reg_no),('acc_year','=',acc_year),('assess_year','=',assess_year)])
            self.pool.get('assessment.window').write(cr,uid,search_ids,{'state':'completed'},context=None)    
        if is_sws:   #### Education Loan
            search_ids = self.pool.get('res.partner').search(cr,uid,[('appli_no','=',application_no)])
            self.pool.get('res.partner').write(cr,uid,search_ids,{'state1':'paid'},context=None)
        if is_sws and type == 'in_invoice':   ### Other SWS non re-fundable
            search_ids = self.pool.get('res.partner').search(cr,uid,[('appli_no','=',application_no)])
            self.pool.get('res.partner').write(cr,uid,search_ids,{'state1':'paid'},context=None)
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
            'assessment_type':fields.selection((('assessment','Direct Assessment'), ('bj','BJ Assessment')),'Assessment Type',required=False), 
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
    _columns = {
                'statement_a':fields.many2one('product.product','Income',domain=[('income', '=', True),('sale_ok', '=', True)],ondelete='set null',required=True),
                'quantity':fields.float('Quantity',size=16),
                'uom':fields.char('UOM',size=16),
                'unit_cost':fields.float('Amount',size=16),
                'amount':fields.function(get_total_multiplication,string='Sub Total',type='float',method=True),
                'description':fields.text('Description'),
                'assess_menu_id1':fields.many2one('assessment.window','Income',ondelete='set null'),
                'amount_total':fields.float('Total Amount',size=16),
                
                
                }
    _defaults = {
        'description':'Income',
        'uom':'Unit',
        'quantity':1,
        
    }
        
assessment_income_line()

class assessment_expense_line(osv.osv):
    
    _name = 'assessment.window.line2'
    def get_total_multiplication(self, cr, uid, ids, fields, arg, context):
        multi={}
        for record in self.browse(cr, uid, ids):
            multi[record.id]= record.quantity * record.unit_cost
        return multi
    _columns = {
                'statement_a':fields.many2one('product.product','Expense',domain=[('expense', '=', True),('sale_ok', '=', True)],ondelete='set null',required=True),
                'quantity':fields.float('Quantity',size=16),
                'uom':fields.char('UOM',size=16),
                'unit_cost':fields.float('Amount',size=16),
                'amount':fields.function(get_total_multiplication,string='Sub Total',type='float',method=True),
                'description':fields.text('Description'),
                'assess_menu_id2':fields.many2one('assessment.window','Expense',ondelete='set null'),
                'amount_total':fields.float('Total Amount',size=16),
                }
    _defaults = {
        'description':'Expense',
        'uom':'Unit',
        'quantity':1
    }
        
assessment_expense_line()



class assessment_window(osv.osv):
    
    _name = 'assessment.window'
    def _total_amount_wakf(self, cr, uid, ids, field_name, arg, context=None):
        val1 = 0
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
            'total_income' : 0,
            }
            for line in order.assess_line_id1:
                val1 += line.amount
            res[order.id]['total_income']=val1          
        return res
    def _total_amount_wakf1(self, cr, uid, ids, field_name, arg, context=None):
        val1 = 0
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
            'amount_total1' : 0,
            }
            for line in order.assess_line_id1:
                val1 += line.amount
            res[order.id]['amount_total1']=val1          
        return res
    def _total_amount_wakf2(self, cr, uid, ids, field_name, arg, context=None):
        val1 = 0
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
            'total_expense' : 0,
            }
            for line in order.assess_line_id2:
                val1 += line.amount
            res[order.id]['total_expense']=val1          
        return res
    def _total_amount_wakf3(self, cr, uid, ids, field_name, arg, context=None):
        val1 = 0
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
            'amount_total2' : 0,
            }
            for line in order.assess_line_id2:
                val1 += line.amount
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
            condition = [('name', '=', reg_no)]
            search_acc = id_self.search(cr,uid,condition,context=context)
            ids_acc = id_self.browse(cr,uid,search_acc)
            acc_year_large = 0
            for val in ids_acc:
                if acc_year_large <= int(val.acc_year):
                    if int(val.acc_year) < int(acc_year):
                        acc_year_large = int(val.acc_year)      
            acc_year_large = str(acc_year_large)
            condition = [('acc_year', '=', acc_year_large),('name', '=', reg_no)]
            search_acc = id_self.search(cr,uid,condition,context=context)
            if search_acc:
                kaivasam = id_self.browse(cr,uid,search_acc)[0].line_1
                bank = id_self.browse(cr,uid,search_acc)[0].line_2
                dhanyam = id_self.browse(cr,uid,search_acc)[0].line_3
                values = {
                            'line_1': kaivasam,
                            'line_2': bank,
                            'line_3': dhanyam,
               
                    }
            else:
                values ={
                            'line_1': 0,
                            'line_2': 0,
                            'line_3': 0,
                              }
                
        return {'value' : values}
    def button_calculate(self,cr,uid,ids,fields,arg,context=None):
        exempted_total = 0
        tot_amount_inc = 0
        exempted_list_of_ids = []
        exempted_list_of_amount = []
        deducted_total = 0
        tot_amount_exp = 0
        deducted_list_of_ids = []
        deducted_list_of_amount = []
        dicti = {}
        for rec in self.browse(cr,uid,ids,context=context):
            dicti[rec.id] = {'exempted':0.0,
                             'deducted':0.0,
                             'total_income_final':0.0,
                             'total_expense_final':0.0
                             }
            for line in rec.assess_line_id1:    ##################  line of income ######################
                property = line.statement_a.id
                amount = line.unit_cost or False
                tot_amount_inc = tot_amount_inc + amount
                property_search = self.pool.get('product.product').search(cr,uid,[('id','=',property),('income','=',True)])
                if property_search:
                    product_browse_percentage = self.pool.get('product.product').browse(cr,uid,property_search)[0].percentage_income
                    exempted_total = exempted_total + amount * product_browse_percentage / 100
                    if product_browse_percentage != 0:
                        exempted_list_of_ids.append(property)  # Exempted IDs
                        exempted_list_of_amount.append(amount)  # Exempted Amount
            for line in rec.assess_line_id2:    ##################  line of Expense ######################
                property = line.statement_a.id
                amount = line.unit_cost or False
                tot_amount_exp = tot_amount_exp + amount
                property_search = self.pool.get('product.product').search(cr,uid,[('id','=',property),('expense','=',True)],context=context)
                if property_search:
                    browse_ids = self.pool.get('product.product').browse(cr,uid,property_search,context=context)[0]
                    expense_percentage = browse_ids.percentage_expense
                    relation = browse_ids.deductable # boolean
                    if relation:
                        related_income = browse_ids.related_id.id  # related income
                        for income in rec.assess_line_id1:
                            if relation == income.statement_a:
                                amount_income = income.unit_cost
                                deducted_total = deducted_total + amount_income * expense_percentage / 100  
                                deducted_list_of_ids.append(property)                                      ## Deducted IDs
                                deducted_list_of_amount.append(amount_income * expense_percentage / 100)   ## Deducted Amount
                    else:
                        if expense_percentage != 0:
                            deducted_total = deducted_total + amount * expense_percentage / 100
                            deducted_list_of_ids.append(property)                                      ## Deducted IDs
                            deducted_list_of_amount.append(amount * expense_percentage / 100)   ## Deducted Amount
            dicti[rec.id]['exempted'] = exempted_total or False
            dicti[rec.id]['deducted'] = deducted_total or False
            dicti[rec.id]['total_income_final'] = tot_amount_inc - exempted_total or False
            dicti[rec.id]['total_expense_final'] = tot_amount_exp - deducted_total or False
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
        return similar_objs[0].id
    
    def on_change_wakf_regno_to_name_new_assess(self, cr, uid, ids, reg_no, context=None):
        values = {}
        id_res_partner = self.pool.get('res.partner')
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
                
        return {'value' : values}
    def action_submit(self, cr, uid, ids, context=None):
        follow_list = []
        dicto = {}
        for rec in self.browse(cr, uid, ids, context=context):
            dicto = {'name':"Submitted",'who':uid,'when':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
            follow_list.append((0,0,dicto))
            self.write(cr, uid, ids, {'state':'submitted','follow_up_id':follow_list})
        return True
    
    def action_sent_notice(self, cr, uid, ids, context=None):
        follow_list = []
        dicto = {}
        for rec in self.browse(cr, uid, ids, context=context):
            dicto = {'name':"Notice Send",'who':uid,'when':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
            follow_list.append((0,0,dicto))
            self.write(cr, uid, ids, {'state':'sent_notice','follow_up_id':follow_list})
        return True
    
    def action_invoice(self, cr, uid, ids, context=None):
        invoice_ids = []
        follow_list = []
        dicto = {}
        for rec in self.browse(cr, uid, ids, context=context):
            dicto = {'name':"Invoiced(Draft)",'who':uid,'when':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
            follow_list.append((0,0,dicto))
            price_unit_income = rec.total_income_final
            new_amount_income = rec.total_income_final
            price_unit_expense = rec.total_expense_final
            new_amount_expense = rec.total_expense_final
            output = rec.wakf_id.id
            acc_year = rec.acc_year.id
            ass_year = rec.assess_year.id
            reg_no = rec.name
            search_ids = self.pool.get('product.product').search(cr,uid,[('name','=',"INCOME")])
            income_id = self.pool.get('product.product').browse(cr,uid,search_ids)[0].id
            search_ids = self.pool.get('product.product').search(cr,uid,[('name','=',"EXPENSE")])
            expense_id = self.pool.get('product.product').browse(cr,uid,search_ids)[0].id
            invoice_ids.append((0,0,{'product_id':income_id,'name':"Income(Processed)",'quantity':1,'price_unit':price_unit_income,'new_amount':new_amount_income,'sws':False}))   # sws =True, 7% calculation disabled
            invoice_ids.append((0,0,{'product_id':expense_id,'name':"Income(Processed)",'quantity':1,'price_unit':-price_unit_expense,'new_amount':-new_amount_expense,'sws':False})) # sws =True, 7% calculation disabled
            self.pool.get('account.invoice').create(cr,uid,{'registration_no':reg_no,'assess_year_saleorder':acc_year,'account_year_saleorder':ass_year,'is_assessment':True,'appli_no':False,'account_id':1,'journal_id':'1','partner_id':output,'invoice_line':invoice_ids,'total_income_saleorder':price_unit_income,'total_expense_saleorder':price_unit_expense})
        self.write(cr, uid, ids, {'state':'invoiced','follow_up_id':follow_list})
        return True
    
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
            self.pool.get('revenue.recovery').create(cr,uid,{'reg_no':reg_no,'partner_id':output,'assess_year':ass_year})
        return True
    
    def action_re_assess(self, cr, uid, ids, context=None):
        follow_list = []
        dicto = {}
        for rec in self.browse(cr, uid, ids, context=context):
            dicto = {'name':"Re-assessment",'who':uid,'when':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
            follow_list.append((0,0,dicto))
            output = rec.wakf_id.id
            acc_year = rec.acc_year.id
            ass_year = rec.assess_year.id
            self.write(cr, uid, ids, {'state':'re-assess','follow_up_id':follow_list})
            search_invoice = self.pool.get('account.invoice').search(cr,uid,[('partner_id','=',output),('assess_year_saleorder','=',acc_year),('account_year_saleorder','=',ass_year),('is_assessment','=',True),('appli_no','=',False),('assessment_type','=','assessment'),('state','=','draft')])
            list_unlink = [ invoice.id for invoice in self.pool.get('account.invoice').browse(cr,uid,search_invoice)]
            self.pool.get('account.invoice').unlink(cr,uid,list_unlink,context=context)
            self.write(cr, uid, ids, {'state':'re-assess','follow_up_id':follow_list})
        return True
    
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        """Allows to delete assessment lines in other states"""
        for rec in self.browse(cr, uid, ids, context=context):
            if rec.state not in ['submitted']:
                raise osv.except_osv(_('Invalid Action!'), _('Cannot delete an Assessment Record which is in state \'%s\'.') %(rec.state,))
        return super(assessment_window, self).unlink(cr, uid, ids, context=context)
    
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
                'assess_line_id2':fields.one2many('assessment.window.line2','assess_menu_id2','Expense'),
                'total_income':fields.function(_total_amount_wakf,multi='sums',string='Total Income',store=False),
                'total_expense':fields.function(_total_amount_wakf2,multi='sums2',string='Total Expense',store=False),
                'assess_amount':fields.function(get_total,string='Difference Amount',store=True,type='float',method=False),
                'amount_total1':fields.function(_total_amount_wakf1,multi='sums1',string='Subtotal',store=False),
                'amount_total2':fields.function(_total_amount_wakf3,multi='sums3',string='Subtotal',store=False),
                'description2':fields.text('Extra info',size=32),
                'line_1':fields.float('kaivasam'),
                'line_2':fields.float('bank'),
                'line_3':fields.float('Dhanyam'),
                'user_id':fields.char('user id',size=16),
                'exempted':fields.function(button_calculate,string='Exempted',type='float',multi='all',store=True,method=False),
                'deducted':fields.function(button_calculate,string='Deductable',type='float',multi='all',store=True,method=False),
                'total_income_final':fields.function(button_calculate,string='Total income',type='float',multi='all',store=True,method=False),
                'total_expense_final':fields.function(button_calculate,string='Total expense',type='float',multi='all',store=True,method=False),
                'showcause_notice_no':fields.char('Showcause Notice No',size=16),
                'showcause_tick':fields.boolean('Showcause tick',size=16),
                'follow_up_id':fields.one2many('follow.up','follow_id','Follow Up'),
                'appeal_no':fields.char('Appeal or Case No',size=16),
                'appeal_details':fields.text('Judgement/Order Details',size=16),
                'appeal_date':fields.date('Judgement/Order Date',size=16),
                'revised':fields.boolean('Revised'),
                'appeal_no':fields.char('Order No',size=16),
                'appeal_details':fields.text('Order Details',size=128),
                'appeal_date':fields.date('Order Date',size=16),
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
                
                }
    _defaults = {
                 'date_from': lambda *a: time.strftime(DEFAULT_SERVER_DATE_FORMAT),
                 'user_id': lambda obj, cr, uid, context: uid,
                 'assess_year': _deflt_ass_year,
                 'showcause_notice_no':"0"
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




