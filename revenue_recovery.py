from osv import osv
from osv import fields


import time

from tools.translate import _
from tools import  DEFAULT_SERVER_DATETIME_FORMAT


class Revenue_Recovery(osv.osv):
    
    _name = 'revenue.recovery'
    _order = "id desc"
 
    def action_send(self, cr, uid, ids, context=None):
        follow_list = []
        invoice_ids = []
        dicto = {}
        for rec in self.browse(cr, uid, ids, context=context):
            dicto = {'name':"RR Send",'who':uid,'when':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
            follow_list.append((0,0,dicto))
            self.write(cr, uid, ids, {'state':'send','follow_up_id':follow_list})
            #################################  Invoice for RR  #######################################
            final = rec.grand_total
            reg_no = rec.reg_no
            ass_year = rec.assess_year.id
            output = rec.partner_id.id
            ##############################################################################################################
            search_ids = self.pool.get('product.product').search(cr,uid,[('name','=',"RR")])
            if not search_ids:
                raise osv.except_osv(_('Warning!'), _('Please create a "RR" property first'))
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
            invoice_ids.append((0,0,{'product_id':income_id,'name':"Income(Processed)",'quantity':1,'price_unit':final,'new_amount':final,'sws':False}))   # sws =True, 7% calculation disabled
            id_create_invoice = self.pool.get('account.invoice').create(cr,uid,{'journal_type':'sale','type':'out_invoice','assessment_type':'rr','registration_no':reg_no,'account_year_saleorder':ass_year,'is_assessment':True,'appli_no':False,'account_id':account_id,'journal_id':journal_id,'partner_id':output,'invoice_line':invoice_ids})
            
        return {
            'type': 'ir.actions.act_window',
            'name': "Invoice form",
            'view_type': 'form',
            'view_mode': 'form',
            'context': context,
            'res_id':id_create_invoice,
            #'domain' : [('order_id','in',sale_ids)],
            'res_model': 'account.invoice',
            'target': 'new',
            'nodestroy': True,}
    
  
    def action_cancel(self, cr, uid, ids, context=None):
        follow_list = []
        dicto = {}
        browse_invoice_open = 0
        browse_invoice_draft = 0
        for rec in self.browse(cr, uid, ids, context=context):
            dicto = {'name':"RR Cancelled",'who':uid,'when':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
            follow_list.append((0,0,dicto))
            #old_state = rec.old_state
            reg_no = rec.reg_no
            ass_year = rec.assess_year.id
            acc_year = rec.account_year.id
            output = rec.partner_id.id
            from_a = rec.from_a
            ##############################################################################################
            search_invoice_draft = self.pool.get('account.invoice').search(cr,uid,[('registration_no','=',reg_no),('partner_id','=',output),('account_year_saleorder','=',ass_year),('assessment_type','=','rr'),('state','=','draft')])
            search_invoice_open = self.pool.get('account.invoice').search(cr,uid,[('registration_no','=',reg_no),('partner_id','=',output),('account_year_saleorder','=',ass_year),('assessment_type','=','rr'),('state','=','open')])
            if search_invoice_draft:
                browse_invoice_draft = self.pool.get('account.invoice').browse(cr, uid, search_invoice_draft)
            if search_invoice_open:
                browse_invoice_open = self.pool.get('account.invoice').browse(cr, uid, search_invoice_open)
            if browse_invoice_open:
                self.pool.get('account.invoice').action_cancel(cr,uid,[browse_invoice_open[0].id],context=context)
                #self.write(cr, uid, ids, {'state':'RR','follow_up_id':follow_list})
            if browse_invoice_draft:
                list_unlink = [ invoice.id for invoice in self.pool.get('account.invoice').browse(cr,uid,search_invoice_draft)]
                self.pool.get('account.invoice').unlink(cr,uid,list_unlink,context=context)
            
            ###############################################################################################
            if from_a == 'assessment':
                search_ids = self.pool.get('assessment.window').search(cr,uid,[('name','=',reg_no),('wakf_id','=',output),('assess_year','=',ass_year),('acc_year','=',acc_year)])
                if search_ids:
                    self.pool.get('assessment.window').write(cr,uid,search_ids,{'state':'sent_notice'},context=None)
            ################################################################################################
            if from_a == 'bj': 
                search_ids = self.pool.get('bj.assessment.window').search(cr,uid,[('reg_no','=',reg_no),('wakf_id','=',output),('assessment_year','=',ass_year),('account_year','=',acc_year)])
                if search_ids:
                    self.pool.get('bj.assessment.window').write(cr,uid,search_ids,{'state':'send'},context=None)
            ##############################################################################
            self.write(cr, uid, ids, {'state':'cancel','follow_up_id':follow_list})
        return True
    
    _columns = {
                'reg_no':fields.integer('Register No:', size=16, required=False),
                'assess_year':fields.many2one('account.fiscalyear','Assessment Year',ondelete='set null',readonly=False),
                'account_year':fields.many2one('account.fiscalyear','Account Year',ondelete='set null',readonly=False),
                'wakf_district':fields.many2one('wakf.district','District',ondelete='set null',readonly=False),
                'recover_amount':fields.float('Recover Amount', size=16, required=False),
                'collection_charge':fields.float('Collection Charge', size=16, required=False),
                'grand_total':fields.float('Grand Total', size=16, required=False),
                'certified_date':fields.date('Certified Date', required=False),
                'approve':fields.boolean('Approve', required=False),
                'certified_date':fields.date('Certified Date', required=False),
                'file_no':fields.char('File No:', size=16, required=False),
                'requisiton_no':fields.char('Requisition No:', size=16, required=False),
                'certificate_no':fields.char('Certificate No:', size=16, required=False),
                'send':fields.boolean('Send', required=False),
                'rr_execute':fields.boolean('RR Execute', required=False),
                'cancel':fields.boolean('Cancel', required=False),
                'cancel_date':fields.date('Cancel Date', required=False),
                'partner_id':fields.many2one('res.partner','Wakf Name',ondelete='set null',readonly=False),
                'company_id': fields.many2one('res.company', 'Company',size=64, required=False, readonly=False),
                'user_id':fields.char('user id',size=16),
                'company_id': fields.many2one('res.company', 'Company', required=False),
                'follow_up_id':fields.one2many('follow.up.rr','follow_id','Follow Up'),
                'old_state':fields.char('old state'),
                'state': fields.selection([
                    ('submitted', 'Created'),
                    ('approve', 'Approved'),
                    ('send', 'RR Send'),
                    ('execute', 'RR Executed'),            
                    ('cancel', 'RR Cancelled'),
                    ],'status', readonly=False),
                'from_a': fields.selection([
                    ('assessment', 'Direct Assessment'),
                    ('bj', 'BJ Assessment'),
                    ],'From Where', readonly=True),
                'company_id': fields.many2one('res.company', 'Company', required=False)
                }
    _defaults={
        'user_id': lambda obj, cr, uid, context: uid,
        'state':'submitted',
        'company_id': lambda self,cr,uid,ctx: self.pool['res.company']._company_default_get(cr,uid,object='revenue.recovery',context=ctx)
     }
Revenue_Recovery()

class follow_up_rr(osv.osv):
    
    _name = 'follow.up.rr'
    
    _columns = {
               'name':fields.char('Action',readonly=True),
               'who':fields.many2one('res.users','Who',readonly=True),
               'when':fields.char('When',readonly=True), 
               'follow_id':fields.many2one('revenue.recovery','FOLLOW UP'),
                
                
                }
follow_up_rr()
