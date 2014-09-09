from osv import osv
from osv import fields

class wakf_assesment_heads(osv.osv):
    """
         Open ERP Model
    """
    _name = 'wakf.assesment.head'
    _description = 'wakf.assesment.head'
 
    _columns = {
            'name':fields.char('Head', size=128, required=True),
            'classification':fields.selection((('income','Income'), ('expense','Expense')),'Classification',required=True),
            'Details':fields.text('Details',required=False),
            'is_assessiable':fields.boolean('Is Assessiable'),
        }
wakf_assesment_heads()