from osv import osv
from osv import fields
from tools.translate import _
from tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
from datetime import date
import time

class Arrear_list(osv.osv):
    
    _name = 'arrear.list'
    _order = "id desc"
    
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
    
    def on_change_wakf_reg_no_to_arrear(self, cr, uid, ids, reg_no,all_wakf, context=None):
        def get_fiscal_id(name):
            search_condition = [('name', '=', name)]
            search_ids = self.pool.get('account.fiscalyear').search(cr, uid, search_condition)
            if search_ids:
                acc_year = self.pool.get('account.fiscalyear').browse(cr, uid, search_ids)[0].id
                return acc_year or False
            else:
                raise osv.except_osv(_('Warning!'), _('Set Fiscal Year for %s')%name)

        values = {}
        invoice_lines1 = []
        id_res_partner = self.pool.get('res.partner')
        output = False
        last_payment_date = 0
        last_payment = 0
        for_year = 0
        number = 0
        assess_current_state =0
        amount_dues = 0
        if reg_no:
            search_condition = [('wakf_reg_no', '=', reg_no)]
            search_ids = id_res_partner.search(cr, uid, search_condition, context=context)
            similar_objs = id_res_partner.browse(cr, uid, search_ids, context=context)
            if similar_objs:
                output = id_res_partner.browse(cr, uid, search_ids, context=context)[0].id
                values = {'wakf_id': output,}
            else:
                invoice_lines1.append((2,0))
                values ={'wakf_id': False,
                         'bj_line_id':invoice_lines1
                         } 
                return {'warning': {
                    'title': _('Warning!'),
                    'message':  _('No Wakf registered with Register No %d')%reg_no,},'value':values,
                }
        if all_wakf == False:
            bj_slab_id = self.pool.get('bj.slab')
            search_condition=[('approved','=',True)]
            key_search = bj_slab_id.search(cr,uid,search_condition)
            if key_search:
                key_browse = bj_slab_id.browse(cr,uid,key_search)[0]
            else:
                raise osv.except_osv(_('Cannot Process!'), _('Please Set BJ Slab First and approve it'))
            invoice_id = self.pool.get('account.invoice')
            registration_id = self.pool.get('res.partner')
            search_condition = [('wakf_reg_no', '=', reg_no)]
            search_ids1 = registration_id.search(cr, uid, search_condition)
            date_year = False
            acc_year_today = False
            today = date.today()
            month_today = today.month
            if month_today <= 3:
                acc_year_today = '%d-%d'%(today.year-1,today.year)   ##   finding acc year from today
                year_today = today.year                              ##
            if month_today >= 4:
                acc_year_today = '%d-%d'%(today.year,today.year+1)   ##   finding acc year from today
                year_today = today.year +1                           ##
            if search_ids1:                    
                date_registration = registration_id.browse(cr,uid,search_ids1)[0].wakf_registration_date
                if date_registration:                              # checking registration date of wakf
                    date_year = (datetime.strptime(date_registration, '%Y-%m-%d')).year
                    date_month = (datetime.strptime(date_registration, '%Y-%m-%d')).month
                    if date_month <= 3:
                        date_year = '%d-%d'%(date_year-1,date_year)
                        year_registration = (datetime.strptime(date_registration, '%Y-%m-%d')).year-1
                    if date_month >= 4:
                        date_year = '%d-%d'%(date_year,date_year+1)
                        year_registration = (datetime.strptime(date_registration, '%Y-%m-%d')).year
                else:                                            
                    invoice_lines1.append((2,0))
                    values = {'bj_line_id':invoice_lines1,
                          'wakf_id': False,
                          'year_pending':0,
                          'year_registration':False,
                          'last_paid':False,
                          'last_paid_amount':False,
                          'for_year': False,
                          'net_income':0, 
                          'net_income_assess':0,
                          'contri_amount':0,
                          }
                    warning_of = {
                        'title': _('Warning!'),
                        'message':  _('First Set Registration Date for Wakf'),}
                    return {'value' : values,'warning':warning_of}
                
            if date_year:   ### if registration date
                previous_list = []
                history_list = []
                assess_year = get_fiscal_id(acc_year_today)
                search_condition = [('registration_no', '=', reg_no) , ('state','=','paid'),]
                search_ids3 = self.pool.get('account.invoice').search(cr, uid, search_condition)
                if search_ids3:   # Paid invoice detected 
                    dummy = 0
                    net = 0
                    for loop in invoice_id.browse(cr,uid,search_ids3):    
                        search_condition = [('id', '=', loop.assess_year_saleorder.id)]
                        search_ids = self.pool.get('account.fiscalyear').search(cr, uid, search_condition, context=context)
                        acc_year_last1 = self.pool.get('account.fiscalyear').browse(cr, uid, search_ids, context=context)[0].name
                        vals = int(acc_year_last1[5:9])
                        if dummy <= vals:
                            dummy = vals
                            last_payment_date=loop.date_invoice
                            last_payment = loop.amount_total
                            for_year = loop.assess_year_saleorder.id            
                    #year_last = int(year_last)                  
                    
                    ###########################################################################################
                rest_year = int(year_today) - year_registration
                if rest_year > 0:
                    last_net_amount_is = 5000
                    for repeat in range(rest_year):
                        year_change = '%s-%s'%(year_registration,year_registration+1)
                        acc_year = get_fiscal_id(year_change)
                        search_condition2 = [('registration_no', '=', reg_no) ,('state','=','open'),('assess_year_saleorder','=',acc_year)]
                        if search_condition2:
                            search_list2 = self.pool.get('account.invoice').search(cr,uid,search_condition2)   
                            if search_list2:
                                assess_current_state = self.pool.get('account.invoice').browse(cr,uid,search_list2)[0].assessment_type or False
                                amount_dues = self.pool.get('account.invoice').browse(cr,uid,search_list2)[0].residual or False
                        if search_list2:    ### No paid for this acc year
                            invoice_lines1.append((0,0,{'reg_no':reg_no,'account_year_line':acc_year,'assessment_year_line':assess_year,'assess_amount':amount_dues,'currently_on':assess_current_state}))
                        year_registration = year_registration+1 
                    rest_year = rest_year - number
                    values = {'arrear_line':invoice_lines1,
                              'year_registration':date_registration,
                              'wakf_id': output,
                                      }
                         
                else:                           ### First assessment                  
                    invoice_lines1.append((2,0))
                    values = {'arrear_line':invoice_lines1,
                          'wakf_id': False,
                          'year_registration':False,
                          }
                    warning_of = {
                        'title': _('Warning!'),
                        'message':  _('Assessments are upto-date for this wakf'),}
                    return {'value' : values,'warning':warning_of}
                    
        else:
            invoice_lines1.append((2,0))
            values = {'arrear_line':invoice_lines1,
                      'wakf_id': False,
                      'year_registration':False,
                  
                      }
            warning_of = {
                    'title': _('Warning!'),
                    'message':  _('First set registration date for wakf'),}
            
            return {'value' : values,'warning':warning_of}
        return {'value' : values}
                                
    def on_change_all_wakf_arrear(self, cr, uid, ids,all_wakf,context=None):
        def get_fiscal_id(name,context=None):
            search_condition = [('name', '=', name)]
            search_ids = self.pool.get('account.fiscalyear').search(cr, uid, search_condition, context=context)
            if search_ids:
                acc_year = self.pool.get('account.fiscalyear').browse(cr, uid, search_ids)[0].id
                return acc_year or False
            else:
                raise osv.except_osv(_('Warning!'), _('Set Fiscal Year for %s')%name)
        values = {}
        invoice_lines1 = []
        output = False
        invoice_lines1 = []
        date_year = False
        acc_year_today = False
        balance_year =False
        last_payment_date = False
        date_registration = False
        for_year = False
        last_payment = False
        number = 0
        id_res_partner = self.pool.get('res.partner')
        search_ids = id_res_partner.search(cr,uid,[])
        if all_wakf:
            previous_list = []
            history_list = []
            for loop in id_res_partner.browse(cr,uid,search_ids):
                reg_no = loop.wakf_reg_no
                if reg_no:
                    search_condition = [('wakf_reg_no', '=', reg_no)]
                    search_ids = id_res_partner.search(cr, uid, search_condition, context=context)
                    similar_objs = id_res_partner.browse(cr, uid, search_ids, context=context)
                    if similar_objs:
                        output = id_res_partner.browse(cr, uid, search_ids, context=context)[0].id
                        values = {'wakf_id': output,}
                    else:
                        invoice_lines1.append((2,0))
                        values ={'wakf_id': False,
                                 'bj_line_id':invoice_lines1
                                 } 
                        return {'warning': {
                            'title': _('Warning!'),
                            'message':  _('No Wakf registered with specified Register No %d')%reg_no,},'value':values,
                        }
                bj_slab_id = self.pool.get('bj.slab')
                search_condition=[('approved','=',True)]
                key_search = bj_slab_id.search(cr,uid,search_condition)
                if key_search:
                    key_browse = bj_slab_id.browse(cr,uid,key_search)[0]
                else:
                    raise osv.except_osv(_('Cannot Process!'), _('Please Set BJ Slab First and approve it'))
                invoice_id = self.pool.get('account.invoice')
                registration_id = self.pool.get('res.partner')
                search_condition = [('wakf_reg_no', '=', reg_no)]
                search_ids1 = registration_id.search(cr, uid, search_condition)
                date_year = False
                acc_year_today = False
                today = date.today()
                month_today = today.month
                if month_today <= 3:
                    acc_year_today = '%d-%d'%(today.year-1,today.year)   ##   finding acc year from today
                    year_today = today.year                              ##
                if month_today >= 4:
                    acc_year_today = '%d-%d'%(today.year,today.year+1)   ##   finding acc year from today
                    year_today = today.year +1                           ##
                if search_ids1:                    
                    date_registration = registration_id.browse(cr,uid,search_ids1)[0].wakf_registration_date
                    if date_registration:                              # checking registration date of wakf
                        date_year = (datetime.strptime(date_registration, '%Y-%m-%d')).year
                        date_month = (datetime.strptime(date_registration, '%Y-%m-%d')).month
                        if date_month <= 3:
                            date_year = '%d-%d'%(date_year-1,date_year)
                            year_registration = (datetime.strptime(date_registration, '%Y-%m-%d')).year-1
                        if date_month >= 4:
                            date_year = '%d-%d'%(date_year,date_year+1)
                            year_registration = (datetime.strptime(date_registration, '%Y-%m-%d')).year
                    
                if date_year and date_registration:   ### if registration date
                    previous_list = []
                    history_list = []
                    assess_year = get_fiscal_id(acc_year_today)
                    search_condition = [('registration_no', '=', reg_no) , ('state','=',"paid"),]
                    search_ids3 = self.pool.get('account.invoice').search(cr, uid, search_condition)
                    if search_ids3:   # Paid invoice detected 
                        dummy = 0
                        net = 0
                        for loop in invoice_id.browse(cr,uid,search_ids3):    
                            search_condition = [('id', '=', loop.assess_year_saleorder.id)]
                            search_ids = self.pool.get('account.fiscalyear').search(cr, uid, search_condition, context=context)
                            acc_year_last1 = self.pool.get('account.fiscalyear').browse(cr, uid, search_ids, context=context)[0].name
                            vals = int(acc_year_last1[5:9])
                            if dummy <= vals:
                                dummy = vals
                                last_payment_date=loop.date_invoice
                                last_payment = loop.amount_total
                                for_year = loop.assess_year_saleorder.id            
                        
                        ###########################################################################################
                    rest_year = int(year_today) - year_registration
                    if rest_year > 0:
                        last_net_amount_is = 5000
                        for repeat in range(rest_year):
                            year_change = '%s-%s'%(year_registration,year_registration+1)
                            acc_year = get_fiscal_id(year_change)
                            search_condition2 = [('registration_no', '=', reg_no) ,('state','=','open'),('assess_year_saleorder','=',acc_year)]
                            if search_condition2:
                                search_list2 = self.pool.get('account.invoice').search(cr,uid,search_condition2)   
                                if search_list2:
                                    assess_current_state = self.pool.get('account.invoice').browse(cr,uid,search_list2)[0].assessment_type or False
                                    amount_dues = self.pool.get('account.invoice').browse(cr,uid,search_list2)[0].residual or False
                            if search_list2:    ### No paid for this acc year
                                invoice_lines1.append((0,0,{'reg_no':reg_no,'account_year_line':acc_year,'assessment_year_line':assess_year,'assess_amount':amount_dues,'currently_on':assess_current_state}))
                            year_registration = year_registration+1                        
                        rest_year = rest_year - number
                        values = {'arrear_line':invoice_lines1,
                              'year_registration':date_registration,
                              'wakf_id': False,
                                      }  
                            
        else:
            invoice_lines1.append((2,0))
            values = {'arrear_line':invoice_lines1,
                      'year_registration':False,
                      'wakf_id': False,
                                      }
            
        return {'value' : values}    
         
    def _total_amount_contribution_arrear(self, cr, uid, ids, field_name, arg, context=None):
        val1 = 0
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
            'contri_amount' : 0,
            }
            for line in order.arrear_line:
                val1 += line.assess_amount
            res[order.id]['contri_amount']=val1          
        return res
    
    _columns = {
             'reg_no':fields.integer('Registration No:',size=16),
             'wakf_id':fields.many2one('res.partner','Wakf Name'),                 
             'year_registration':fields.date('Registration Year'),
             'assessment_year':fields.many2one('account.fiscalyear','Assessment Year',ondelete='set null',readonly=True),
             'contri_amount':fields.function(_total_amount_contribution_arrear,multi='sums1',string='Total Dues',store=True),
             'arrear_line':fields.one2many('arrear.line','arrear_line'),
             'user_id':fields.char('user id',size=16),
             'company_id': fields.many2one('res.company', 'Company', required=False),
             'all_wakf':fields.boolean('ALL'),
        }
    
    _defaults={
        'user_id': lambda obj, cr, uid, context: uid,
        'company_id': lambda self,cr,uid,ctx: self.pool['res.company']._company_default_get(cr,uid,object='arrear.list',context=ctx),
        'assessment_year':_deflt_ass_year,
        'all_wakf':True,
     }
Arrear_list()


class Arrear_line(osv.osv):

    _name = 'arrear.line'
 
    _columns = {
                
         'reg_no':fields.integer('Register No',size=8),
         'arrear_line':fields.many2one('arrear.list','Arrear Line',ondelete='set null',required=False),
         'account_year_line':fields.many2one('account.fiscalyear','Account Year',ondelete='set null'),
         'assessment_year_line':fields.many2one('account.fiscalyear','Assessment Year',ondelete='set null'),
         'assess_amount':fields.float('Due Amount'),
         'currently_on':fields.selection((('assessment','Direct Assessment'), ('bj','BJ Assessment'),('rr','Revenue Recovery')),'Currently on',required=False),                                         
                }
        
Arrear_line()