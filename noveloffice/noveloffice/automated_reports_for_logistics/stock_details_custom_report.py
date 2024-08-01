import frappe
import pandas as pd
import os
from frappe.utils.file_manager import save_file, get_file

def create_stock_detail_report():
    current_date = frappe.utils.getdate()
    
    from_date = frappe.utils.getdate('2023-04-01')
    to_date = current_date

    report1 = frappe.get_doc('Report', 'Stock Projected Qty')
    report_filters1 = {'company': 'VIBGYOR NET CONNECTIONS PVT LTD'}
    report_data1 = report1.get_data(filters=report_filters1)

    report2 = frappe.get_doc('Item-Wise Purchase Register Custom', f'{from_date}-{to_date}')

    existing_doc = frappe.get_list('Stock Details Custom Report', filters = {'date': str(current_date)})

    if existing_doc:
        report_doc = frappe.get_doc('Stock Details Custom Report', str(current_date))
    else:
        report_doc = frappe.new_doc('Stock Details Custom Report')
        report_doc.date = current_date
        

    report_values = []
    skip = True
    
    for item1 in report_data1:
        if skip:
            skip = False
            continue
        length = len(item1)
        for index, values in enumerate(item1):
            if index != length - 1:
                for item2 in report2.report:
                    max_date = frappe.utils.getdate('2019-03-31')
                    if item2.item_code == values['item_code'] and frappe.utils.getdate(item2.posting_date) >= max_date:
                        max_date = item2.posting_date
                        rate = item2.rate
                        ageing = abs(frappe.utils.date_diff(current_date, item2.posting_date))
                        report_values.append({'Part Code': values['item_code'],
                                            'Description': values['description'],
                                            'UOM': values['stock_uom'],
                                            'Pysical Qty Available in warehouse': values['actual_qty'],
                                            'Ordered Qty to R&M': values['ordered_qty'],
                                            'Reserved/Blocked Qty': values['reserved_qty'],
                                            'Free Stock': values['actual_qty'] - values['reserved_qty'],
                                            'Item Rate': rate,
                                            'age': ageing
                                            })
                                
                    
                
    df = pd.DataFrame(report_values)  
    writer = pd.ExcelWriter(f'/home/frappe/frappe-bench/apps/erpnext/erpnext/selling/report/automated_reports_for_logistics/excel_sheets/Stock Details-{current_date}.xlsx', engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Stock Details', startrow=1, header=False, index=False)
    workbook = writer.book
    worksheet = writer.sheets['Stock Details']
    (max_row, max_col) = df.shape
    column_settings = []
    for header in df.columns:
        column_settings.append({'header': header})
    worksheet.add_table(0, 0, max_row, max_col - 1, {'columns': column_settings})
    worksheet.set_column(0, max_col - 1, 12)
    writer.close()

    new_doc = frappe.new_doc('Logistics Report Attachments')
    new_doc.date = current_date
    new_doc.report_name = f'Stock Details-{current_date}'
    new_doc.insert()
    url = [{'file_url' : ''}]
    
    file_data = open(f'/home/frappe/frappe-bench/apps/erpnext/erpnext/selling/report/automated_reports_for_logistics/excel_sheets/Stock Details-{current_date}.xlsx', 'rb').read()
    file_attach = save_file(f'Stock Details report - {current_date}.xlsx', file_data, 'Logistics Report Attachments', new_doc.name)
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
    # recipient = ['mohammed.s@noveloffice.in']
    subject = f'Stock Details report - {current_date}'
    message = '''Hello Team,<br>
    <br>
    PFA, for the updated stock details as of 7:00 AM today.'''
    frappe.sendmail(
    recipients= recipient,
    bcc = ['mohammed.s@noveloffice.in'],
    subject=subject,
    message=message,
    attachments= url,
    expose_recipients= 'header',
    now = True
    )

    directory_path = f'/home/frappe/frappe-bench/apps/erpnext/erpnext/selling/report/automated_reports_for_logistics/excel_sheets/'

    if os.path.exists(directory_path):
        files = os.listdir(directory_path)
        for file_name in files:
            file_path = os.path.join(directory_path, file_name)
            os.remove(file_path)


    

