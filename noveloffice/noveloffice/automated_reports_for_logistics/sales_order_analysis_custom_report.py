import frappe
import pandas as pd
from frappe.utils.file_manager import save_file, get_file
import os

def create_so_analysis_report():
    
    report = frappe.get_doc('Report', 'Sales Order Analysis')
    current_date = frappe.utils.getdate()
    from_date = frappe.utils.getdate('2023-04-01')
    to_date = current_date
    report_filters = {'company': 'VIBGYOR NET CONNECTIONS PVT LTD', 'from_date': from_date, 'to_date': to_date}
    report_data = report.get_data(filters=report_filters)
    # log(report_data)
    existing_doc = frappe.get_list('Sales Order Analysis Custom Report', filters = {'from_date': from_date,
                                                                                    'to_date': to_date
    })
    if existing_doc:
        so_doc = frappe.get_doc('Sales Order Analysis Custom Report', f'{from_date}-{to_date}')
    else:
        so_doc = frappe.new_doc('Sales Order Analysis Custom Report')
        so_doc.company = report_filters['company']
        so_doc.from_date = from_date
        so_doc.to_date = to_date

    stock_projected_report = frappe.get_doc('Report', 'Stock Projected Qty')    
    skip = True
    report_values = []
    item_price = 0
    for item in report_data:
        if skip:
            skip = False
            continue
        length = len(item)
        
        for index, values in enumerate(item):
            if index != length -1:
                report_filters = {'company': 'VIBGYOR NET CONNECTIONS PVT LTD', 'warehouse': 'Kudlu Gate - VNCPL', 'item_group': 'Products', 'item_code': values.item_code}
                report_data1 = stock_projected_report.get_data(filters=report_filters)
                skip1 = True
                for item in report_data1:
                    if skip1:
                        skip1 = False
                        continue
                    if item:
                        warehouse_stock = item[0]['actual_qty']
                        break
                sales_doc = frappe.get_doc('Sales Order', values.sales_order)
                for item in sales_doc.items:
                    if item.item_code == values.item_code:
                        item_price = item.rate
                report_values.append({'date': values.date,
                                'sales_order': values.sales_order,
                                'status': values.status,
                                'customer': values.customer,
                                'item_code': values.item_code,
                                'description': values.description,
                                'qty': values.qty,
                                'delivered_qty': values.delivered_qty,
                                'qty_to_deliver': values.pending_qty,
                                'billed_qty': values.billed_qty,
                                'qty_to_bill': values.qty_to_bill,
                                'amount': values.amount,
                                'billed_amount': values.billed_amount,
                                'pending_amount': values.pending_amount,
                                'amount_delivered': values.delivered_qty_amount,
                                'delivery_date': values.delivery_date,
                                'delay_in_days': values.delay,
                                'time_taken_to_deliver': values.time_taken_to_deliver,
                                'warehouse': values.warehouse,
                                'company': values.company,
                                'warehouse_stock': warehouse_stock,
                                'item_price': item_price
                                
                })
            else:
                print(values)
                report_values.append({'date': 'Total',
                                    'sales_order': values[0],
                                    'status': values[1],
                                    'customer': values[2],
                                    'item_code': values[3],
                                    'description': values[4],
                                    'qty': values[6],
                                    'delivered_qty': values[7],
                                    'qty_to_deliver': values[8],
                                    'billed_qty': values[9],
                                    'qty_to_bill': values[10],
                                    'amount': values[11],
                                    'billed_amount': values[12],
                                    'pending_amount': values[13],
                                    'amount_delivered': values[14],
                                    'delivery_date': values[15],
                                    'delay_in_days': values[16],
                                    'time_taken_to_deliver': values[17],
                                    'warehouse': values[18],
                                    'company': values[19]
                                    
                    })
                   
    df = pd.DataFrame(report_values)  

    so_doc.set('report', {})
    so_doc.extend('report', report_values) 
    so_doc.save()   

    writer = pd.ExcelWriter(f'/home/frappe/frappe-bench/apps/erpnext/erpnext/selling/report/automated_reports_for_logistics/excel_sheets/SO Analysis & Abstract-{current_date}.xlsx', engine='xlsxwriter')
    df.to_excel(writer, sheet_name='SO Analysis', startrow=1, header=False, index=False)
    workbook = writer.book
    worksheet = writer.sheets['SO Analysis']
    (max_row, max_col) = df.shape
    column_settings = []
    for header in df.columns:
        column_settings.append({'header': header})
    worksheet.add_table(0, 0, max_row, max_col - 1, {'columns': column_settings})
    worksheet.set_column(0, max_col - 1, 12)
    


    #Sales Order Abstract Automation
    existing_doc1 = frappe.get_list('Sales Order Abstract', filters={'from_date': str(from_date),
                                                                'to_date': str(to_date)}
                                                                )
    if existing_doc1:
        so_doc = frappe.get_doc('Sales Order Abstract', f'{str(from_date)}-{str(to_date)}')
    else:
        so_doc = frappe.new_doc('Sales Order Abstract')
        so_doc.from_date = str(from_date)
        so_doc.to_date = str(to_date)
        so_doc.save()
        
    combined_query = frappe.db.sql(f'''
        SELECT
            DISTINCT sa.customer,
            available_items.sales_order,
            available_items.total_column_value,
            pending_amount.total_pending_amount
        FROM
            (SELECT
                sales_order,
                SUM(
                    CASE
                        WHEN qty_to_deliver = 0 THEN 0
                        WHEN warehouse_stock >= qty_to_deliver THEN item_price * qty_to_deliver
                        ELSE item_price * warehouse_stock
                    END
                ) AS total_column_value
            FROM
                `tabSales Order Analysis Child Report`
            WHERE
                parent = "{from_date}-{to_date}"
            GROUP BY
                sales_order) as available_items
        JOIN
            (SELECT
                sales_order,
                SUM(pending_amount) AS total_pending_amount
            FROM
                `tabSales Order Analysis Child Report`
            WHERE
                status != 'Completed'
                AND parent = "{from_date}-{to_date}"
            GROUP BY
                sales_order
            HAVING
                total_pending_amount > 0) as pending_amount
        ON available_items.sales_order = pending_amount.sales_order
        JOIN
            `tabSales Order Analysis Child Report` as sa
        ON sa.sales_order = available_items.sales_order;
    ''')

    report_values1 = []
    for values in combined_query:
        if not values[0] and not values[1]:
            continue
        report_values1.append({'customer': values[0],
                            'sales_order': values[1],
                            'open_so_amount': values[3],
                            'available_items_for_sales_amount': values[2]
        })
        
    df1 = pd.DataFrame(report_values1)

    so_doc.set('summary', {})
    so_doc.extend('summary', report_values1)
    so_doc.save()

    print(df)  
    # writer = pd.ExcelWriter(f'/home/frappe/frappe-bench/apps/erpnext/erpnext/selling/report/automated_reports_for_logistics/excel_sheets/SO Abstract-{current_date}.xlsx', engine='xlsxwriter')
    df1.to_excel(writer, sheet_name='SO Abstract', startrow=1, header=False, index=False)
    second_worksheet = writer.sheets['SO Abstract']
    (max_row, max_col) = df1.shape
    column_settings = []
    for header in df1.columns:
        column_settings.append({'header': header})
    second_worksheet.add_table(0, 0, max_row, max_col - 1, {'columns': column_settings})
    second_worksheet.set_column(0, max_col - 1, 12)
    writer.close()

    new_doc = frappe.new_doc('Logistics Report Attachments')
    new_doc.date = current_date
    new_doc.report_name = f'SO Analysis & Abstract-{current_date}'
    new_doc.insert()
    url = [{'file_url' : ''}]
    
    file_data = open(f'/home/frappe/frappe-bench/apps/erpnext/erpnext/selling/report/automated_reports_for_logistics/excel_sheets/SO Analysis & Abstract-{current_date}.xlsx', 'rb').read()
    file_attach = save_file(f'SO Analysis & Abstract-{current_date}.xlsx', file_data, 'Logistics Report Attachments', new_doc.name)
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
    subject = f'SO Analysis & Abstract report - {current_date}'
    message = '''Hello Team,<br>
    <br>
    PFA, for the updated SO Analysis & Abstract report as of 7:00 AM today.'''
    frappe.sendmail(
    recipients= recipient,
    bcc=['mohammed.s@noveloffice.in'],
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
