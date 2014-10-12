from osv import osv
from osv import fields
from tools import  DEFAULT_SERVER_DATETIME_FORMAT
from datetime import date
import time
from tools.translate import _


class bj_assessment_window(osv.osv):
    _name = 'bj.assessment.window'
    _order = "id desc"
    def on_change_confirm_bj(self, cr, uid, ids, context=None):
        invoice_ids = []
        for key in self.browse(cr,uid,ids,context=context):
            reg_no = key.reg_no
            output = key.wakf_id.id
            bj_line_id = key.bj_line_id
            for bj_line in key.bj_line_id:
                product_id = 3
                name = "BJ"
                quantity = 1
                price_subtotal = bj_line.net_income1
                price_unit = bj_line.net_income1
                new_amount = bj_line.net_income1
                acc_year = bj_line.account_year_line.id
                invoice_ids.append((0,0,{'product_id':product_id,'name':name,'quantity':quantity,'price_subtotal':price_subtotal,'price_unit':price_unit,'new_amount':new_amount}))
                self.pool.get('account.invoice').create(cr,uid,{'is_assessment':True,'registration_no':reg_no,'account_id':1,'journal_id':'1','partner_id':output,'invoice_line':invoice_ids,'assess_year_saleorder':acc_year,'assessment_type':'bj'})
                invoice_ids = []
            self.write(cr, uid, ids, {'state':'approved'})
        return False
    
    
    def _total_amount_net_bj(self, cr, uid, ids, field_name, arg, context=None):
        val1 = 0
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
            'total_income' : 0,
            }
            for line in order.bj_line_id:
                val1 += line.net_income1
            res[order.id]['net_income']=val1          
        return res
    def _total_amount_net_Assess(self, cr, uid, ids, field_name, arg, context=None):
        val1 = 0
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
            'total_income' : 0,
            }
            for line in order.bj_line_id:
                val1 += line.assess_amount
            res[order.id]['net_income_assess']=val1          
        return res
    def _total_amount_contribution_bj(self, cr, uid, ids, field_name, arg, context=None):
        val1 = 0
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
            'total_income' : 0,
            }
            for line in order.bj_line_id:
                val1 += line.contri_amount1
            res[order.id]['contri_amount']=val1          
        return res
    def _deflt_ass_year(self, cr, uid, ids, context=None):
        today = date.today()
        month_of = today.month
        if month_of <= 3:
            date_of = '%d-%d'%(today.year-1,today.year)
        if month_of >= 4:
            date_of = '%d-%d'%(today.year,today.year+1)
        company_id = self.pool['res.company']._company_default_get(cr,uid,object='case.registration'),
        search_condition = [('name', '=', date_of),('company_id','=',company_id)]
        search_ids = self.pool.get('account.fiscalyear').search(cr, uid, search_condition, context=context)
        if search_ids:
            similar_objs = self.pool.get('account.fiscalyear').browse(cr, uid, search_ids, context=context)
        if similar_objs:
            return similar_objs[0].id
        return False
   
    def action_approve(self, cr, uid, ids, context=None):
        follow_list = []
        dicto = {}
        for rec in self.browse(cr, uid, ids, context=context):
            dicto = {'name':"Approved",'who':uid,'when':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
            follow_list.append((0,0,dicto))
            self.write(cr, uid, ids, {'state':'approved','follow_line_id':follow_list})
        return True
    def action_send(self, cr, uid, ids, context=None):
        follow_list = []
        dicto = {}
        invoice_ids = []
        for rec in self.browse(cr, uid, ids, context=context):
            dicto = {'name':"BJ Send",'who':uid,'when':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
            follow_list.append((0,0,dicto))
            price_unit_income = rec.net_bj or False
            new_amount_income = rec.net_bj or False
            output = rec.wakf_id.id or False
            acc_year = rec.account_year.id or False
            ass_year = rec.assessment_year.id or False
            reg_no = rec.reg_no or False
            ##############################################################################################################
            search_ids = self.pool.get('product.product').search(cr,uid,[('name','=',"BJ")])
            if not search_ids:
                raise osv.except_osv(_('Warning!'), _('Please create a "BJ" property first'))
            income_id = self.pool.get('product.product').browse(cr,uid,search_ids)[0].id
            
            search_ids = self.pool.get('account.account').search(cr,uid,[('name','=',"Accounts Receivable")])
            if not search_ids:
                raise osv.except_osv(_('Warning!'), _('Please create an account "Accounts Receivable" first'))
            account_id = self.pool.get('account.account').browse(cr,uid,search_ids)[0].id
            
            search_ids = self.pool.get('account.journal').search(cr,uid,[('name','=',"Assessment Journal")])
            if not search_ids:
                raise osv.except_osv(_('Warning!'), _('Please create "Assessment Journal" First'))
            journal_id = self.pool.get('account.journal').browse(cr,uid,search_ids)[0].id
            ##############################################################################################################
            invoice_ids.append((0,0,{'product_id':income_id,'name':"BJ Assessment",'quantity':1,'price_unit':price_unit_income,'new_amount':new_amount_income,'sws':False}))   # sws =True, 7% calculation disabled
            self.pool.get('account.invoice').create(cr,uid,{'registration_no':reg_no,'assess_year_saleorder':acc_year,'account_year_saleorder':ass_year,'is_assessment':True,'appli_no':False,'account_id':account_id,'journal_id':journal_id,'partner_id':output,'invoice_line':invoice_ids,'total_income_saleorder':False,'total_expense_saleorder':False,'assessment_type':'bj'})
        self.write(cr, uid, ids, {'state':'send','follow_line_id':follow_list})
        return True
    def action_cancel(self, cr, uid, ids, context=None):
        follow_list = []
        dicto = {}
        for rec in self.browse(cr, uid, ids, context=context):
            dicto = {'name':"BJ Cancelled",'who':uid,'when':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
            follow_list.append((0,0,dicto))
            self.write(cr, uid, ids, {'state':'cancelled','follow_line_id':follow_list})
        return True
    
    def action_re_assessment(self, cr, uid, ids, context=None):
        follow_list = []
        dicto = {}
        for rec in self.browse(cr, uid, ids, context=context):
            dicto = {'name':"Cancelled and Re-Assessment",'who':uid,'when':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
            follow_list.append((0,0,dicto))
            output = rec.wakf_id.id or False
            acc_year = rec.account_year.id or False
            ass_year = rec.assessment_year.id or False
            self.write(cr, uid, ids, {'state':'re_assessment','follow_line_id':follow_list})
            search_invoice = self.pool.get('account.invoice').search(cr,uid,[('partner_id','=',output),('assess_year_saleorder','=',acc_year),('account_year_saleorder','=',ass_year),('is_assessment','=',True),('appli_no','=',False),('assessment_type','=','bj'),('state','=','draft')])
            list_unlink = [ invoice.id for invoice in self.pool.get('account.invoice').browse(cr,uid,search_invoice)]
            self.pool.get('account.invoice').unlink(cr,uid,list_unlink,context=context)
        return True
    
    def action_rr(self, cr, uid, ids, context=None):
        follow_list = []
        dicto = {}
        browse_invoice_draft = 0
        browse_invoice_open = 0
        for rec in self.browse(cr, uid, ids, context=context):
            dicto = {'name':"Send RR",'who':uid,'when':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
            follow_list.append((0,0,dicto))
            reg_no = rec.reg_no
            output = rec.wakf_id.id or False
            acc_year = rec.account_year.id or False
            ass_year = rec.assessment_year.id or False
            #############################################
            search_invoice_draft = self.pool.get('account.invoice').search(cr,uid,[('partner_id','=',output),('assess_year_saleorder','=',acc_year),('account_year_saleorder','=',ass_year),('is_assessment','=',True),('appli_no','=',False),('assessment_type','=','bj'),('state','=','draft')])
            search_invoice_open = self.pool.get('account.invoice').search(cr,uid,[('partner_id','=',output),('assess_year_saleorder','=',acc_year),('account_year_saleorder','=',ass_year),('is_assessment','=',True),('appli_no','=',False),('assessment_type','=','bj'),('state','=','open')])
            search_invoice_paid = self.pool.get('account.invoice').search(cr,uid,[('partner_id','=',output),('assess_year_saleorder','=',acc_year),('account_year_saleorder','=',ass_year),('is_assessment','=',True),('appli_no','=',False),('assessment_type','=','bj'),('state','=','paid')])
            if search_invoice_draft:
                browse_invoice_draft = self.pool.get('account.invoice').browse(cr, uid, search_invoice_draft)
            if search_invoice_open:
                browse_invoice_open = self.pool.get('account.invoice').browse(cr, uid, search_invoice_open)
            if browse_invoice_open:
                self.pool.get('account.invoice').action_cancel(cr,uid,[browse_invoice_open[0].id],context=context)
            if browse_invoice_draft:
                list_unlink = [ invoice.id for invoice in self.pool.get('account.invoice').browse(cr,uid,search_invoice_draft)]
                self.pool.get('account.invoice').unlink(cr,uid,list_unlink,context=context)
            self.write(cr, uid, ids, {'state':'rr','follow_line_id':follow_list})
            
            ##############################################################################################
            ##########################################  RR Created  ##########################################
            id_create = self.pool.get('revenue.recovery').create(cr,uid,{'from_a':'bj','reg_no':reg_no,'partner_id':output,'assess_year':ass_year,'account_year':acc_year})
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
        return True
    
    def showcause(self, cr, uid, ids, context=None):
        acc_year_1 = False
        acc_year = False
        for key in self.browse(cr,uid,ids,context=context):
            reg_no = key.reg_no
            output = key.wakf_id.id
            amount = key.contri_amount
            assessment_year=key.assessment_year.id
            count = 0
            for bj_line in key.bj_line_id:
                if count == 0:
                    acc_year_1 = bj_line.account_year_line.id
                acc_year = bj_line.account_year_line.id
                count += 1          
            self.pool.get('show.cause').create(cr,uid,{'reg_no':reg_no,'assessment_year':assessment_year,'acc_year_from':acc_year_1,'partner_id':output,'acc_year_to':acc_year,'amount':amount})
            self.write(cr, uid, ids, {'state':'showcause'})
        return False
    
    ##################################################################################################
    #                                    CANNOT DELETE BJ ASSESSMENT RECORDS                         #
    #                                                TESTED
    ##################################################################################################
    
    #def unlink(self, cr, uid, ids, context=None):
    #    if context is None:
    #        context = {}
    #    """Allows to delete assessment lines in other states"""
    #    for rec in self.browse(cr, uid, ids, context=context):
    #        if rec.state not in ['draft']:
    #            raise osv.except_osv(_('Invalid Action!'), _('Cannot delete an Assessment Record which is in state \'%s\'.') %(rec.state,))
    #    return super(bj_assessment_window, self).unlink(cr, uid, ids, context=context)
    

    
    _columns = {
         'reg_no':fields.integer('Registration No:',size=16),
         'wakf_id':fields.many2one('res.partner','Wakf Name'),
         'ass_date':fields.date('Assessment Date',size=16),
         'net_assess':fields.float('Net Income(Assessment)'),
         'net_bj':fields.float('Net Income(BJ)'),
         'contribution':fields.float('Contribution'),                
         'assessment_year':fields.many2one('account.fiscalyear','Assessment Year',ondelete='set null'),
         'account_year':fields.many2one('account.fiscalyear','Account Year',ondelete='set null'),
         'follow_line_id':fields.one2many('follow.up.bj','follow_id','FOLLOW UPs'),
         'state':fields.selection((('draft','Draft'), ('approved','BJ Confirmed'),('send','BJ Send'),('re_assessment','Re-Assessment'),('rr','RR Send'),('cancelled','BJ Cancelled'),('completed','BJ Completed')),'BJ State',required=False), 
         'user_id':fields.char('user id',size=16), 
         'company_id': fields.many2one('res.company', 'Company', required=False)                              
                }
    _defaults ={
                'assessment_year':_deflt_ass_year,
                'state':'approved',
                'user_id': lambda obj, cr, uid, context: uid,
                'company_id': lambda self,cr,uid,ctx: self.pool['res.company']._company_default_get(cr,uid,object='bj.assessment.window',context=ctx)
                }
bj_assessment_window()

class follow_up_bj(osv.osv):
    
    _name = 'follow.up.bj'
    
    _columns = {
               'name':fields.char('Action',readonly=True),
               'who':fields.many2one('res.users','Who',readonly=True),
               'when':fields.char('When',readonly=True), 
               'follow_id':fields.many2one('bj.assessment.window','FOLLOW UP'),
                
                
                }
follow_up_bj()



