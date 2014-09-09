from osv import osv
from osv import fields

class wakf_assesment(osv.osv):
    """
         Open ERP Model
    """
    _name = 'wakf.assesment'
    _description = 'wakf.assesment'
 
    _columns = {
            'name':fields.char('name', size=128, required=True),
            'wakf_id':fields.many2one('res.partner','Wakf Name',required=True,ondelete='set null'),
            
            'assesment_date_from':fields.date('From Date',required=True),
            'assesment_date_to':fields.date('To Date',required=True),
            'total_income':fields.float('Total Income'),
            'total_expense':fields.float('Total Expense'),
            'assesment_amount':fields.float('Assesment Amount',required=True),
            'contribution_amount':fields.float('Contribution Amount',required=True),
            'income_id':fields.one2many('wakf.assesment.income','assesment_id','Incomes'),
            'expense_id':fields.one2many('wakf.assesment.expense','assesment_id','Incomes'),
            
        }
wakf_assesment()

class wakf_assesment_income(osv.osv):
    
    _name = 'wakf.assesment.income'
    _description = 'wakf.assesment.income'
    
    _columns={
              'assesment_id':fields.many2one('wakf.assesment','Assesment',ondelete="set null"),
              'assesment_head_id':fields.many2one('wakf.assesment.head','Head',ondelete="set null"),
              'name':fields.char('name', size=128, required=False),
              'amount':fields.float('Amount',required=True),
              'quantity':fields.float('Quantity',required=True),
              'unit':fields.selection((('cent','Cent'), ('kg','Kg'), ('hector','Hector')),'Unit',required=False),             
              }
    
wakf_assesment_income()  

class wakf_assesment_expense(osv.osv):
    
    _name = 'wakf.assesment.expense'
    _description = 'wakf.assesment.expense'
    
    _columns={
              'assesment_id':fields.many2one('wakf.assesment','Assesment',ondelete="set null"),
              'assesment_head_id':fields.many2one('wakf.assesment.head','Head',ondelete="set null"),
              'name':fields.char('name', size=128, required=False),
              'amount':fields.float('Amount',required=True),
              'quantity':fields.float('Quantity',required=True),
              'unit':fields.selection((('cent','Cent'), ('kg','Kg'), ('hector','Hector')),'Unit',required=False),              
              }
    
wakf_assesment_expense()