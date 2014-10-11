from osv import osv
from osv import fields
from tools.translate import _

from tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
from datetime import date
import time


class bj_assessment(osv.osv):
    _name = 'bj.assessment'
    _order = "id desc"
    def refresh_amount(self, cr, uid, ids, context=None):
        """Method is used to show form view in new windows"""
        this = self.browse(cr, uid, ids, context=None)
        return this
    
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
    
    def on_change_wakf_regno_to_name_new_assess(self, cr, uid, ids, reg_no,all_wakf, context=None):
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
                    'message':  _('No Wakf registered with specified Register No'),},'value':values,
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
                    #year_last = int(year_last)                  
                    
                    ###########################################################################################
                rest_year = int(year_today) - year_registration
                if rest_year > 0:
                    last_net_amount_is = 5000
                    for repeat in range(rest_year):
                        year_change = '%s-%s'%(year_registration,year_registration+1)
                        acc_year = get_fiscal_id(year_change)
                        search_condition = [('registration_no', '=', reg_no) , ('state','=',"paid"),('assess_year_saleorder','=',acc_year)]
                        search_list = self.pool.get('account.invoice').search(cr,uid,search_condition)
                        if search_list:    ### Paid Invoice detected
                            browse_list = self.pool.get('account.invoice').browse(cr,uid,search_list)[0]
                            paid_amount = browse_list.net_amount
                            year_reg = date_registration
                            acc_year = browse_list.assess_year_saleorder.id
                            pay_date = browse_list.date_invoice
                            contri_amnt = browse_list.amount_total
                            history_list.append((0,0,{'year_registration':year_reg,'for_year':acc_year,'last_paid':pay_date,'last_paid_amount':contri_amnt}))
                            previous_list.append(paid_amount) 
                            number = number + 1     
                        if not search_list:    ### No paid for this acc year
                            if repeat == 0:
                                last_net_amount_is = 5000
                            else:
                                last_net_amount_is = previous_list[-1]
                            for harry in key_browse.slab_id:
                                if harry.bj_amount_start<=last_net_amount_is<harry.bj_amount_end:  #### checking BJ slab ###
                                    percentage = harry.percentage
                                    bj_amount = last_net_amount_is + last_net_amount_is * percentage / 100  ### Returning BJ amount with increment
                                    #year_change = '%s-%s'%(year_registration,year_registration+1)
                                    acc_year = get_fiscal_id(year_change)              ### checking BJ itself
                                    ###########################################  BJ ASSESSMENT CHECK  ###################################
                                    search_condition = [('reg_no', '=', reg_no) , ('state','in',['approved','send','rr','completed']),('account_year','=',acc_year)]
                                    search_list1 = self.pool.get('bj.assessment.window').search(cr,uid,search_condition)
                                    ###########################################  BJ ASSESSMENT CHECK  ###################################
                                    #===================================================================================================#
                                    #===================================================================================================#
                                    ###########################################   ASSESSMENT CHECK  ###################################
                                    search_condition = [('name', '=', reg_no) , ('state','in',['submitted','sent_notice','invoiced','showcause','RR','appeal','re-assess','completed']),('acc_year','=',acc_year)]
                                    search_list2 = self.pool.get('assessment.window').search(cr,uid,search_condition)
                                    ###########################################   ASSESSMENT CHECK  ###################################
                                    #===================================================================================================#
                                    #===================================================================================================#
                                    ###########################################  INVOICE CHECK  ###################################
                                    search_condition = [('registration_no', '=', reg_no) , ('state','in',['open','paid']),('assess_year_saleorder','=',acc_year)]
                                    search_list3 = self.pool.get('account.invoice').search(cr,uid,search_condition)
                                    ###########################################  INVOICE CHECK  ###################################
                                    if not search_list1 or search_list2 or search_list3:
                                        invoice_lines1.append((0,0,{'reg_no':reg_no,'account_year_line':acc_year,'assessment_year_line':assess_year,'assess_amount':last_net_amount_is,'net_income1':bj_amount,'contri_amount1':bj_amount*7/100}))
                                        last_net_amount_is = last_net_amount_is + bj_amount*7/100 
                                    if search_list1 or search_list2 or search_list3:
                                        number = number + 1
                                    previous_list.append(last_net_amount_is)
                        year_registration = year_registration+1 
                    rest_year = rest_year - number
                    values = {'bj_line_id':invoice_lines1,
                              'bj_history_id':history_list,
                              'year_pending':rest_year,
                              'year_registration':date_registration,
                              'last_paid':last_payment_date or False,
                              'last_paid_amount':last_payment,
                              'for_year': for_year,
                              'wakf_id': output,
                              'net_income':0, 
                              'net_income_assess':0,
                              'contri_amount':0,
                                      }
                         
                else:                           ### First assessment                  
                    invoice_lines1.append((2,0))
                    values = {'bj_line_id':invoice_lines1,
                          'bj_history_id':False,    
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
                        'message':  _('Assessments are upto-date for this wakf'),}
                    return {'value' : values,'warning':warning_of}
                    
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
                    'message':  _('First set registration date for wakf'),}
            
            return {'value' : values,'warning':warning_of}
        return {'value' : values}
    def on_change_all_wakf_bj(self, cr, uid, ids,all_wakf,context=None):
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
                            'message':  _('No Wakf registered with specified Register No'),},'value':values,
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
                            search_condition = [('registration_no', '=', reg_no) , ('state','=',"paid"),('assess_year_saleorder','=',acc_year)]
                            search_list = self.pool.get('account.invoice').search(cr,uid,search_condition)
                            if search_list:    ### Paid Invoice detected
                                browse_list = self.pool.get('account.invoice').browse(cr,uid,search_list)[0]
                                paid_amount = browse_list.net_amount
                                year_reg = date_registration
                                acc_year = browse_list.assess_year_saleorder.id
                                pay_date = browse_list.date_invoice
                                contri_amnt = browse_list.amount_total
                                history_list.append((0,0,{'year_registration':year_reg,'for_year':acc_year,'last_paid':pay_date,'last_paid_amount':contri_amnt}))
                                previous_list.append(paid_amount) 
                                number = number + 1     
                            if not search_list:    ### No paid for this acc year
                                if repeat == 0:
                                    last_net_amount_is = 5000
                                else:
                                    last_net_amount_is = previous_list[-1]
                                for harry in key_browse.slab_id:
                                    if harry.bj_amount_start<=last_net_amount_is<harry.bj_amount_end:  #### checking BJ slab ###
                                        percentage = harry.percentage
                                        bj_amount = last_net_amount_is + last_net_amount_is * percentage / 100  ### Returning BJ amount with increment
                                        #year_change = '%s-%s'%(year_registration,year_registration+1)
                                        acc_year = get_fiscal_id(year_change)              ### checking BJ itself
                                        ###########################################  BJ ASSESSMENT CHECK  ###################################
                                        search_condition = [('reg_no', '=', reg_no) , ('state','in',['approved','send','rr','completed']),('account_year','=',acc_year)]
                                        search_list1 = self.pool.get('bj.assessment.window').search(cr,uid,search_condition)
                                        ###########################################  BJ ASSESSMENT CHECK  ###################################
                                        #===================================================================================================#
                                        #===================================================================================================#
                                        ###########################################   ASSESSMENT CHECK  ###################################
                                        search_condition = [('name', '=', reg_no) , ('state','in',['submitted','sent_notice','invoiced','showcause','RR','appeal','re-assess','completed']),('acc_year','=',acc_year)]
                                        search_list2 = self.pool.get('assessment.window').search(cr,uid,search_condition)
                                        ###########################################   ASSESSMENT CHECK  ###################################
                                        #===================================================================================================#
                                        #===================================================================================================#
                                        ###########################################  INVOICE CHECK  ###################################
                                        search_condition = [('registration_no', '=', reg_no) , ('state','in',['open','paid']),('assess_year_saleorder','=',acc_year)]
                                        search_list3 = self.pool.get('account.invoice').search(cr,uid,search_condition)
                                        ###########################################  INVOICE CHECK  ###################################
                                        if not search_list1 or search_list2 or search_list3:
                                            invoice_lines1.append((0,0,{'reg_no':reg_no,'account_year_line':acc_year,'assessment_year_line':assess_year,'assess_amount':last_net_amount_is,'net_income1':bj_amount,'contri_amount1':bj_amount*7/100}))
                                            last_net_amount_is = last_net_amount_is + bj_amount*7/100 
                                        if search_list1 or search_list2 or search_list3:
                                            number = number + 1
                                        previous_list.append(last_net_amount_is)
                            year_registration = year_registration+1 
                        rest_year = rest_year - number
                        values = {'bj_line_id':invoice_lines1,
                                  #'bj_history_id':history_list,
                                  'year_pending':rest_year,
                                  'year_registration':False,
                                  'last_paid':last_payment_date or False,
                                  'last_paid_amount':False,
                                  'for_year': False,
                                  'wakf_id': False,
                                  'net_income':0, 
                                  'net_income_assess':0,
                                  'contri_amount':0,
                                          }  
                            
        else:
            invoice_lines1.append((2,0))
            values = {'bj_line_id':invoice_lines1,
                      'bj_history_id':False,
                      'wakf_id': False,
                      'year_pending':0,
                      'year_registration':False,
                      'last_paid':False,
                      'last_paid_amount':False,
                      'for_year': False,
                      'net_income':0, 
                      'net_income_assess':0,
                      'contri_amount':0,
                      'reg_no':False
                      }
            
        return {'value' : values}
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
        for rec in self.browse(cr, uid, ids, context=None):
            keep = [rec.bj_line_id]
            self.write(cr, uid, ids, {'bj_line_id':[(2,0)]})
        self.write(cr, uid, ids, {'state':'created','bj_line_id':keep})
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
    

    
    _columns = {
         'reg_no':fields.integer('Registration No:',size=16),
         'wakf_id':fields.many2one('res.partner','Wakf Name'),                 
         'assess_year':fields.char('Assessment Year:',size=16),
         'account_year':fields.date('Account Year'),
         'assessment_year':fields.many2one('account.fiscalyear','Assessment Year',ondelete='set null',readonly=True),
         'year_pending':fields.char('Year Pending:',size=16,readonly=False),
         'year_registration':fields.date('Year of Registration:',readonly=True),
         'last_paid':fields.date('Last Paid on:',readonly=True),
         'last_paid_amount':fields.float('Last Paid Amount:',size=16,readonly=True),
         'for_year':fields.many2one('account.fiscalyear','For account Year',ondelete='set null',readonly=True),
         'net_income_assess':fields.function(_total_amount_net_Assess,multi='sums2',string='Net Income(Assessment)',store=True),
         'net_income':fields.function(_total_amount_net_bj,multi='sums',string='Net Income(BJ)',store=True), 
         'contri_amount':fields.function(_total_amount_contribution_bj,multi='sums1',string='Total Contribution',store=True),
         'bj_line_id':fields.one2many('bj.assessment.line','bj_line'),
         'bj_history_id':fields.one2many('bj.assessment.line.history','history_line',readonly=True),
         'all_wakf':fields.boolean('All wakf ?'),
         'user_id':fields.char('user id',size=16),
         'state':fields.selection((('draft','Draft'),('created','Authenticated'), ('approved','BJ Confirmed'),('showcause','ShowCause')),'BJ State',required=False), 
         'company_id': fields.many2one('res.company', 'Company', required=False)                
                }
    _defaults ={
                'assessment_year':_deflt_ass_year,
                'all_wakf':True,
                'state':'draft',
                'user_id': lambda obj, cr, uid, context: uid,
                'company_id': lambda self,cr,uid,ctx: self.pool['res.company']._company_default_get(cr,uid,object='bj.assessment',context=ctx)
                }
bj_assessment()

class bj_assessment_line(osv.osv):
    _name = 'bj.assessment.line'
    
    
    def button_bj(self, cr, uid, ids, context):
        id_res_partner = self.pool.get('res.partner')
        for rec in self.browse(cr,uid,ids,context=context):
            reg_no = rec.reg_no
            ass_date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            net_assess = rec.assess_amount
            net_bj = rec.net_income1
            contribution = rec.contri_amount1
            assessment_year = rec.assessment_year_line.id
            account_year = rec.account_year_line.id
            search_condition = [('wakf_reg_no', '=', reg_no)]
            search_ids = id_res_partner.search(cr, uid, search_condition, context=context)
            wakf_id = id_res_partner.browse(cr, uid, search_ids, context=context)[0].id or False
            id_create = self.pool.get('bj.assessment.window').create(cr,uid,{'reg_no':reg_no,'ass_date':ass_date,'net_assess':net_assess,'net_bj':net_bj,'contribution':contribution,'assessment_year':assessment_year,'account_year':account_year,'wakf_id':wakf_id})
        self.unlink(cr,uid,ids)
        return {
            'type': 'ir.actions.act_window',
            'name': "BJ Assessment Window form",
            'view_type': 'form',
            'view_mode': 'form',
            'context': context,
            'res_id':id_create,
            #'domain' : [('order_id','in',sale_ids)],
            'res_model': 'bj.assessment.window',
            'target': 'new',
            'nodestroy': True,}
    
    
    _columns = {
         'reg_no':fields.char('Register No',size=8,readonly=True),
         'bj_line':fields.many2one('bj.assessment','BJ Line',ondelete='set null'),
         'account_year_line':fields.many2one('account.fiscalyear','Account Year',ondelete='set null',readonly=True),
         'assessment_year_line':fields.many2one('account.fiscalyear','Assessment Year',ondelete='set null',readonly=True),
         'assess_amount':fields.float('Assessment Amount',size=16,readonly=True),
         'net_income1':fields.float('BJ Amount',size=16,readonly=True), 
         'contri_amount1':fields.float('Contribution',size=16,readonly=True),
          
                                        
                }
bj_assessment_line()

