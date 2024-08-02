import frappe
 
class Calculate:
    def __init__(self):
        self.current_month = frappe.utils.getdate().month
        self.current_year = frappe.utils.getdate().year
        self.first_of_date = str(self.current_year) + "-" + str(self.current_month) + "-01"
        self.convert_first_of_date = frappe.utils.getdate(self.first_of_date)
       
        # Compute the total number of days in the current month
        self.num_of_days = self.get_total_days_in_current_month(self.current_year, self.current_month)
 
        # Define the start and end date of the current month
        self.current_month_start_date_str = str(self.current_year) + "-" + str(self.current_month) + "-01"
        self.current_month_end_date_str = str(self.current_year) + "-" + str(self.current_month) + "-" + str(self.num_of_days)
        self.current_month_start_date = frappe.utils.getdate(self.current_month_start_date_str)
        self.current_month_end_date = frappe.utils.getdate(self.current_month_end_date_str)
 
    def add_new_record(self, arr):
        doc1 = frappe.new_doc("Sales Invoice vs Leads")
        doc1.insert()
        name1 = doc1.name
        for i in arr:
            doc1.append('revenue_comparsion', {
                "leads": i['lead'],
                "leads_revenue": i['l_revenue'],
                "sales_invoice_revenue": i['s_revenue']
            })
        doc1.save()
        frappe.rename_doc('Sales Invoice vs Leads', name1, frappe.utils.nowdate())
 
    def is_leap_year(self, year):
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
 
    def get_total_days_in_current_month(self, current_year1, current_month1):
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if self.is_leap_year(current_year1) and current_month1 == 2:
            return 29
        return days_in_month[current_month1 - 1]
 
    def sum_sales_invoice(self, lead):
        data = frappe.db.sql('''
                select distinct parent from `tabSales Invoice Item`
                where start_date >= %s and stop_date <= %s and parenttype = "Sales Invoice" and parent in
                (select name from `tabSales Invoice` where lead_name = %s);
               ''', (self.current_month_start_date, self.current_month_end_date, lead), as_dict=True)
        sum_tot = 0
        for i in data:
            doc = frappe.get_doc("Sales Invoice", i.parent)
            child_table = doc.items
            for j in child_table:
                item_code1 = j.item_code
                amount1 = j.amount
                if item_code1!="Interest on Debtors":
                    sum_tot = sum_tot + amount1 
        return round(sum_tot, 2)
 
    def sum_client_items_table(self, lead):
        doc1 = frappe.get_doc("Leads", lead)
        return float(doc1.total_revenue)
 
    def sum_facility_one_time_billing(self, lead):
        doc = frappe.get_doc("Leads", lead)
        child_table = doc.facility
        sum_tot = 0
        for i in child_table:
            start_date1_todate = frappe.utils.getdate(i.start_date)
            stop_date1_todate = frappe.utils.getdate(i.end_date)
            if ((start_date1_todate.month >= self.current_month) and (start_date1_todate.year >= self.current_year)) and ((stop_date1_todate.month <= self.current_month) and (stop_date1_todate.year <= self.current_year)):
                sum_tot += i.amount
        return sum_tot
 
    def sum_facility_mr_cr_br_tr(self, lead):
        doc = frappe.get_doc("Leads", lead)
        child_table = doc.facility
        sum_tot = 0
        for i in child_table:
            start_date1_todate = frappe.utils.getdate(i.start_date)
            if ((start_date1_todate.month >= self.current_month) and (start_date1_todate.year >= self.current_year)) and ((frappe.utils.getdate(i.end_date).month <= self.current_month) and (frappe.utils.getdate(i.end_date).year <= self.current_year)):
                if frappe.utils.getdate().month == start_date1_todate.month and frappe.utils.getdate().year == start_date1_todate.year:
                    sum_tot += i.amount
        return sum_tot
 
    def execute_sales_invoice_vs_leads_revenue(self):
        arr = []
        data1 = frappe.db.sql('''
            SELECT
                name, customer_name
            FROM
                `tabLeads`
            WHERE 
                customer_name != '' AND
                leasing_status != "On Notice" AND 
                leasing_status != "Ex-Client"
        ''', as_dict=True)
        
        lead_ids = []
           
        for i in data1:
            if not i['customer_name'].endswith("(PSLLC)"):
                lead_ids.append(i['name'])
 
        for lead in lead_ids:
            client_items_result = self.sum_client_items_table(lead)
            facility_one_time_billing_result = self.sum_facility_one_time_billing(lead)
            sum_facility_mr_cr_br_tr_result = self.sum_facility_mr_cr_br_tr(lead)
            tot_revenue_leads = round((client_items_result + facility_one_time_billing_result + sum_facility_mr_cr_br_tr_result), 2)
            tot_revenue_sales_invoice = self.sum_sales_invoice(lead)
            arr.append({"lead": lead, "l_revenue": tot_revenue_leads , "s_revenue": tot_revenue_sales_invoice})
        self.add_new_record(arr)
 
def execute_sales_invoice_vs_leads_revenue_class():
    c = Calculate()
    c.execute_sales_invoice_vs_leads_revenue()
 
def execute_sales_invoice_vs_leads_revenue_class_enqueue():
    frappe.enqueue(execute_sales_invoice_vs_leads_revenue_class, queue = 'long')
 
 