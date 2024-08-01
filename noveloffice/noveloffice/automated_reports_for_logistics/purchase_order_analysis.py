import frappe
import pandas as pd
from frappe.utils.file_manager import save_file, get_file
import os
import math
def create_po_analysis_report():
        
    current_date = frappe.utils.getdate()
    from_date = frappe.utils.getdate('2023-04-01')
    to_date = current_date

    report = frappe.get_doc('Report', 'Purchase Order Analysis')

    report_filters = {'company': 'VIBGYOR NET CONNECTIONS PVT LTD', 'from_date': from_date, 'to_date': to_date}
    report_data = report.get_data(filters=report_filters)

    existing_doc = frappe.get_list('Purchase Order Analysis Custom Report', filters = {'from_date': str(from_date),
                                                                                    'to_date': str(to_date)
    })
    if existing_doc:
        po_doc = frappe.get_doc('Purchase Order Analysis Custom Report', f'{str(from_date)}-{str(to_date)}')
    else:
        po_doc = frappe.new_doc('Purchase Order Analysis Custom Report')
        po_doc.company = report_filters['company']
        po_doc.from_date = str(from_date)
        po_doc.to_date = str(to_date)

    skip = True
    report_values = []
    for item in report_data:
        if skip:
            skip= False
            continue
        length = len(item)
        for index, values in enumerate(item):
            if index != length -1:
                report_values.append({'date': values.date,
                                'required_by': values.required_date,
                                'purchase_order': values.purchase_order,
                                'status': values.status,
                                'supplier': values.supplier,
                                'project': values.project,
                                'item_code': values.item_code,
                                'qty': values.qty,
                                'received_qty': values.received_qty,
                                'pending_qty': values.pending_qty,
                                'billed_qty': values.billed_qty,
                                'qty_to_bill': values.qty_to_bill,
                                'amount': values.amount,
                                'billed_amount': values.billed_amount,
                                'pending_amount': values.pending_amount,
                                'received_qty_amount': values.received_qty_amount,
                                'warehouse': values.warehouse,
                                'company': values.company,
                                    })
            else:
                print(values)
                report_values.append({'date': 'Total',
                                'required_by': values[0],
                                'purchase_order': values[1],
                                'status': values[2],
                                'supplier': values[3],
                                'project': values[4],
                                'item_code': values[5],
                                'qty': values[7],
                                'received_qty': values[8],
                                'pending_qty': values[9],
                                'billed_qty': values[10],
                                'qty_to_bill': values[11],
                                'amount': values[12],
                                'billed_amount': values[13],
                                'pending_amount': values[14],
                                'received_qty_amount': values[15],
                                'warehouse': values[16],
                                'company': values[17],
                                    })

                      
    df = pd.DataFrame(report_values)  

    po_doc.set('report', {})
    po_doc.extend('report', report_values) 
    po_doc.save()   

    writer = pd.ExcelWriter(f'/home/frappe/frappe-bench/apps/erpnext/erpnext/selling/report/automated_reports_for_logistics/excel_sheets/PO Analysis & Abstract-{current_date}.xlsx', engine='xlsxwriter')
    df.to_excel(writer, sheet_name='PO Analysis', startrow=1, header=False, index=False)
    workbook = writer.book
    worksheet = writer.sheets['PO Analysis']
    (max_row, max_col) = df.shape
    column_settings = []
    for header in df.columns:
        column_settings.append({'header': header})
    worksheet.add_table(0, 0, max_row, max_col - 1, {'columns': column_settings})
    


    #Sales Order Abstract Automation
    existing_doc1 = frappe.get_list('Purchase Order Abstract', filters={'from_date': str(from_date),
                                                                'to_date': str(to_date)}
                                                                )
    if existing_doc1:
        po_doc = frappe.get_doc('Purchase Order Abstract', f'{str(from_date)}-{str(to_date)}')
    else:
        po_doc = frappe.new_doc('Purchase Order Abstract')
        po_doc.from_date = str(from_date)
        po_doc.to_date = str(to_date)
        po_doc.save()
        
    query = frappe.db.sql(f'''SELECT
                purchase_order,
                supplier,
                SUM(pending_amount) AS total_pending_amount
            FROM
                `tabPurchase Order Analysis Child Table`
            WHERE
                status != 'Completed'
                AND parent = "{from_date}-{to_date}"
            GROUP BY
                purchase_order
            HAVING
                total_pending_amount > 0''')
                
    report_values1 = []
    total_amount = 0
    for values in query:
        if not values[0] and not values[1]:
            continue
        total_amount = total_amount + values[2]
        report_values1.append({'vendor_name': values[1],
                            'purchase_order': values[0],
                            'open_po_amount': values[2],
        })
    
        
    
    report_values1.append({'vendor_name': 'Total',
                           'open_po_amount': total_amount})
    
    df1 = pd.DataFrame(report_values1)
    
    po_doc.total = total_amount
    po_doc.set('summary', {})
    po_doc.extend('summary', report_values1)
    po_doc.save()

    print(df)  
    # writer = pd.ExcelWriter(f'/home/frappe/frappe-bench/apps/erpnext/erpnext/selling/report/automated_reports_for_logistics/excel_sheets/PO Abstract-{current_date}.xlsx', engine='xlsxwriter')
    df1.to_excel(writer, sheet_name='PO Abstract', startrow=1, header=False, index=False)
    workbook = writer.book
    second_worksheet = writer.sheets['PO Abstract']
    (max_row, max_col) = df1.shape
    column_settings = []
    for header in df1.columns:
        column_settings.append({'header': header})
    second_worksheet.add_table(0, 0, max_row, max_col - 1, {'columns': column_settings})
    second_worksheet.set_column(0, max_col - 1, 12)
    writer.close()

    new_doc = frappe.new_doc('Logistics Report Attachments')
    new_doc.date = current_date
    new_doc.report_name = f'PO Analysis & Abstract-{current_date}'
    new_doc.insert()
    url = [{'file_url' : ''}]
    
    file_data = open(f'/home/frappe/frappe-bench/apps/erpnext/erpnext/selling/report/automated_reports_for_logistics/excel_sheets/PO Analysis & Abstract-{current_date}.xlsx', 'rb').read()
    file_attach = save_file(f'PO Analysis & Abstract-{current_date}.xlsx', file_data, 'Logistics Report Attachments', new_doc.name)
    file_list = frappe.get_list("File",
            filters = {
                'attached_to_name' : new_doc.name
            },
            as_list = True,
            )
    # print(file_list[0][0])
    file = frappe.get_doc("File",file_list[0][0])
    url[0]['file_url'] = file.file_url
    new_doc.attachment = file.file_url
    new_doc.save()
    print(url)
    recipient = ['orders@vibgyornet.com']
    subject = f'PO Analysis & Abstract report - {current_date}'
    message = '''Hello Team,<br>
    <br>
    PFA, for the updated PO Analysis & Abstract report as of 7:00 AM today.'''
    frappe.sendmail(
    recipients= recipient,
    bcc = ['mohammed.s@noveloffice.in'],
    subject=subject,
    message=message,
    attachments= url,
    expose_recipients= 'header',
    now = True
    )

    # new_doc = frappe.new_doc('Logistics Report Attachments')
    # new_doc.date = current_date
    # new_doc.report_name = f'PO Abstract-{current_date}'
    # new_doc.insert()
    # url = [{'file_url' : ''}]
    
    # file_data = open(f'/home/frappe/frappe-bench/apps/erpnext/erpnext/selling/report/automated_reports_for_logistics/excel_sheets/PO Abstract-{current_date}.xlsx', 'rb').read()
    # file_attach = save_file(f'PO Abstract report - {current_date}.xlsx', file_data, 'Logistics Report Attachments', new_doc.name)
    # file_list = frappe.get_list("File",
    #         filters = {
    #             'attached_to_name' : new_doc.name
    #         },
    #         as_list = True,
    #         )
    # # print(file_list[0][0])
    # file = frappe.get_doc("File",file_list[0][0])
    # url[0]['file_url'] = file.file_url
    # new_doc.attachment = file.file_url
    # new_doc.save()
    # print(url)
    # recipient = ['mohammed.s@noveloffice.in', 'suresh.t@vibgyornet.com']
    # subject = f'PO Abstract report - {current_date}'
    # message = '''Hello Team,<br>
    # <br>
    # PFA, for the updated PO Abstract report as of 7:00 AM today.'''
    # frappe.sendmail(
    # recipients= recipient,
    # subject=subject,
    # message=message,
    # attachments= url,
    # expose_recipients= 'header',
    # now = True
    # )

    directory_path = f'/home/frappe/frappe-bench/apps/erpnext/erpnext/selling/report/automated_reports_for_logistics/excel_sheets/'

    if os.path.exists(directory_path):
        files = os.listdir(directory_path)
        for file_name in files:
            file_path = os.path.join(directory_path, file_name)
            os.remove(file_path)
