import frappe

def custom_leads_backup():
    doc_tuple = frappe.get_list('Leads', filters ={
        'leasing_status': ['in', ['Client', 'On Notice', 'Deposit Received', 'Token Received']]
    }, as_list = True)
    doc_list = [item[0] for item in doc_tuple]
    today = frappe.utils.getdate()

    for doc in doc_list:
        try:
            copy_client_item_table = []
            copy_otb_table = []
            copy_mr_cr_table = []
            lead_doc = frappe.get_doc('Leads', doc)
            duplicate_doc = frappe.new_doc('Leads Client Items Table Backup')
            duplicate_doc.lead_id = lead_doc.name
            duplicate_doc.date = frappe.utils.add_days(today, -1)
            duplicate_doc.customer_id = lead_doc.customer_name
            for items in lead_doc.item:
                copy_client_item_table = frappe.copy_doc(items)
                copy_client_item_table.linked_id = items.name
                duplicate_doc.append('items_child_table', copy_client_item_table)
            duplicate_doc.save()
            for amenity in lead_doc.amenity_recursion:
                copy_client_amenity_table = frappe.copy_doc(amenity)
                copy_client_amenity_table.linked_id = amenity.name
                duplicate_doc.append('amenity_recursion', copy_client_amenity_table)
            duplicate_doc.save()
            for facilities in lead_doc.facility:
                copy_otb_table = frappe.copy_doc(facilities)
                # copy_otb_table.linked_id = facilities.name
                duplicate_doc.append('facility_one_time_billing', copy_otb_table)
            duplicate_doc.save()
            for facilities2 in lead_doc.facility2:
                copy_mr_cr_table = frappe.copy_doc(facilities2)
                # copy_mr_cr_table.linked_id = facilities2.name
                duplicate_doc.append('facility_mr_cr_br_tr', copy_mr_cr_table)
            duplicate_doc.save()
        except Exception as e:
            error_doc = frappe.new_doc('Error log for Scheduler Scripts')
            error_doc.id = f'Error in Leads Client Items for Facility Table Backup'
            error_doc.lead_name = doc
            error_doc.customer_name = lead_doc.customer_name
            error_doc.script_name = '7_days_backup_of_client_items_and_faiclity_tables'
            error_doc.error = str(e)
            error_doc.save()
            continue
                            

    three_days_in_past = frappe.utils.add_days(today,-7)
    leads_delete = frappe.db.sql(f"SELECT name FROM `tabLeads Client Items Table Backup` WHERE date < '{three_days_in_past}'")
    for del_lead in leads_delete:
        frappe.delete_doc("Leads Client Items Table Backup", del_lead[0])


def custom_leads_backup_enqueue():
    frappe.enqueue(custom_leads_backup, queue = 'long')