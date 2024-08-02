import frappe

def execute_reconcilitation_customer_list():
	reconciliation_details = []
	today = frappe.utils.getdate()
	doc = frappe.new_doc("Reconciliation Customer List")
	ex_client_doc = frappe.new_doc("Reconciliation Customer List")
	exempt_customer_list = ["M. Sarasa", "S Vinod Reddy", "S Pramod Reddy", "M Shama Reddy", "Suspense Account (C)", "HDFC Bank Limited", "Pramila Elecon", "Hassan Gowdaiah Sukanya", "Bedegere Sudhanva Sidharth"]

	# Create a string with placeholders for the exempted customers
	exempt_customer_string = ', '.join(['%s' for i in exempt_customer_list])

	# Use the placeholders in the SQL query and pass the exempt_customer_list as parameters
	customer_list = frappe.db.sql(f"""
		SELECT name 
		FROM `tabCustomer` 
		WHERE (location NOT IN ('PROJECTS', 'LOGISTICS') OR location IS NULL)
		AND name NOT IN (SELECT name FROM `tabCompany`)
		AND name NOT IN ({exempt_customer_string})
	""", tuple(exempt_customer_list), as_dict=True)

	for customer in customer_list:
		try:
			sales_invoice_list = frappe.db.sql(f'''SELECT name, company, outstanding_amount 
											FROM `tabSales Invoice` 
											WHERE customer = "{customer.name}" 
											AND status IN ('Unpaid', 'Partly Paid', 'Overdue')
											''', as_dict=True)

			payment_entry_list = frappe.db.sql(f'''SELECT name, company, unallocated_amount
											FROM `tabPayment Entry`
											WHERE party = "{customer.name}"
											AND docstatus = 1
											AND unallocated_amount > 0
											''', as_dict=True)

			tds_payment_entry_list = frappe.db.sql(f'''SELECT pe.name, pe.company,
															pd.amount
													FROM `tabPayment Entry` AS pe
													INNER JOIN `tabPayment Entry Deduction` AS pd
													ON pe.name = pd.parent
													WHERE pe.party = "{customer.name}"
													AND pe.docstatus = 1
													AND pd.account LIKE '%TDS Receivable%'
													''', as_dict=True)
													
			journal_entry_list = frappe.db.sql(f'''SELECT je.name, je.company, 
												SUM(jea.credit) - SUM(jea.debit) AS balance
												FROM `tabJournal Entry Account` AS jea
												INNER JOIN `tabJournal Entry` AS je
												ON jea.parent = je.name
												WHERE je.docstatus = 1
												AND jea.account LIKE 'Customer Refundable Deposit%'
												AND jea.party = "{customer.name}"
												GROUP BY je.name, je.company''', as_dict=True)

			deposit_payment_entry_list = frappe.db.sql(f'''SELECT pe.name, pe.company,
															pd.amount
													FROM `tabPayment Entry` AS pe
													INNER JOIN `tabPayment Entry Deduction` AS pd
													ON pe.name = pd.parent
													WHERE pe.party = "{customer.name}"
													AND pe.docstatus = 1
													AND pd.account LIKE '%Customer Refundable Deposit%'
													''', as_dict=True)

			
			total_pending_amount_journal_entry_list = frappe.db.sql(f'''SELECT je.name, je.company, jea.party,
														(SUM(jea.debit) - SUM(jea.credit)) AS balance
														FROM `tabJournal Entry Account` AS jea
														INNER JOIN `tabJournal Entry` AS je
														ON jea.parent = je.name
														WHERE je.docstatus = 1
														AND jea.account LIKE '%Accounts Receivable (Debtors)%'
														AND jea.party = "{customer.name}"
														GROUP BY je.name, je.company''', as_dict=True)
														
			for je_entry in total_pending_amount_journal_entry_list:
				pe = frappe.db.sql(f"""Select per.reference_name, per.allocated_amount from `tabPayment Entry Reference` AS per INNER JOIN `tabPayment Entry` AS pe
					ON per.parent = pe.name
					WHERE
					pe.docstatus = 1
					AND pe.party = "{je_entry['party']}"
					AND per.reference_name = "{je_entry['name']}"
					""", as_dict=True)
				
				for pe_entry in pe:
					je_entry['balance'] = round(je_entry['balance'] - pe_entry['allocated_amount'], 2)

			tds_journal_entry_list = frappe.db.sql(f'''SELECT je.name, je.company,
												SUM(jea.credit) - SUM(jea.debit) AS tds_balance
												FROM `tabJournal Entry Account` AS jea
												INNER JOIN `tabJournal Entry` AS je
												ON jea.parent = je.name
												WHERE je.docstatus = 1
												AND jea.account LIKE '%TDS Receivable%'
												AND jea.party = "{customer.name}"
												GROUP BY je.name, je.company''', as_dict=True)

			company_list = set()
			
			# Iterate through payment_entry_list
			for entry in sales_invoice_list:
				company_list.add(entry['company'])
				
			# Iterate through payment_entry_list
			for entry in payment_entry_list:
				company_list.add(entry['company'])
				
			# Iterate through tds_payment_entry_list
			for entry in tds_payment_entry_list:
				company_list.add(entry['company'])
				
			# Iterate through journal_entry_list
			for entry in journal_entry_list:
				company_list.add(entry['company'])
				
			for entry in deposit_payment_entry_list:
				company_list.add(entry['company'])
				
			for entry in total_pending_amount_journal_entry_list:
				company_list.add(entry['company'])
				
			# Iterate through tds_journal_entry_list
			for entry in tds_journal_entry_list:
				company_list.add(entry['company'])
			
			# Now, company_list contains unique company names
			for company in company_list:
				total_deposit_amount = 0
				debit_pending_tds = 0
				credit_pending_tds = 0
				sales_invoice_deposit = 0
				payment_entry_deposit = 0
				balance_refundable_amount = 0
				total_pending_amount_journal_entry_deposit = 0
			
				# Calculate deposit for the company from journal_entry_list
				for entry in journal_entry_list:
					if entry['company'] == company:
						total_deposit_amount = total_deposit_amount + entry['balance']
				
				for entry in deposit_payment_entry_list:
					if entry['company'] == company:
						total_deposit_amount = total_deposit_amount - entry['amount']
						

			
				# Calculate debit_pending_tds for the company from tds_payment_entry_list
				for entry in tds_payment_entry_list:
					if entry['company'] == company:
						debit_pending_tds = debit_pending_tds + entry['amount']
			
				# Calculate credit_pending_tds for the company from tds_journal_entry_list
				for entry in tds_journal_entry_list:
					if entry['company'] == company:
						credit_pending_tds = credit_pending_tds + entry['tds_balance']
						
						
				total_pending_tds_amount = debit_pending_tds - credit_pending_tds

				for entry in sales_invoice_list:
					if entry['company'] == company:
						sales_invoice_deposit = sales_invoice_deposit + entry['outstanding_amount']

				for entry in payment_entry_list:
					if entry['company'] == company:
						payment_entry_deposit = payment_entry_deposit + entry['unallocated_amount']

				for entry in total_pending_amount_journal_entry_list:
					if entry['company'] == company:
						total_pending_amount_journal_entry_deposit = total_pending_amount_journal_entry_deposit + entry['balance']
				
				total_pending_amount = sales_invoice_deposit - payment_entry_deposit + total_pending_amount_journal_entry_deposit

				company_location_dict = {
					"POLISETTY SOMASUNDARAM" : ["NTP"],
					"VIBGYOR NET CONNECTIONS" : ["NOC"],
					"Millertech Spaces LLP" : ["BTP3F", "NOM"],
					"Estetic Spaces LLP (formerly known as 'Novel Office Centre LLP')" : ["BTP1F", "NOQ", "NBP"],
					"Novel Triton LLP" : ["NBP"],
					"Civana Spaces LLP (formerly known as 'Novel Cassini LLP')" : ["NOW"],
				}
					
				if -10 <= total_pending_tds_amount <= 10:
					total_pending_tds_amount = 0
				balance_refundable_amount = total_deposit_amount - total_pending_tds_amount - total_pending_amount
					
				confirmed_location = company_location_dict.get(company, None)
				if confirmed_location:
					confirmed_location_str = ', '.join(f'"{loc}"' for loc in confirmed_location)
					# Use the IN clause in the SQL query
					lead_query = f'''SELECT name 
										FROM `tabLeads`
										WHERE confirmed_location IN ({confirmed_location_str})
										AND customer_name = "{customer.name}"'''

					lead = frappe.db.sql(lead_query, as_dict=True)
					lead_total_revenue = 0
					if lead:
						usd_deposit_amount = frappe.db.sql(f'''SELECT * FROM `tabUSD Deposit Amount for Leads` WHERE customer = "{customer.name}"''', as_dict = True)
						if usd_deposit_amount:
							total_deposit_amount = total_deposit_amount + float(usd_deposit_amount[0]['deposit_amount'])
						lead_string = ''
						lead_string = ', '.join(f'{lead_entry.name}' for lead_entry in lead)
						for lead_entry in lead:
							lead_doc = frappe.get_doc("Leads", lead_entry['name'])
							
							if lead_doc.total_revenue != 0:
								deposit_in_months = lead_doc.deposit/lead_doc.total_revenue
							
							# Assuming lead has a field named 'total_revenue'
							lead_total_revenue = lead_total_revenue + lead_doc.total_revenue
							number_of_seats = lead_doc.number_of_seats
			
							# current_month_revenue = lead.total_revenue
							total_month_revenue_with_gstAmount = lead_total_revenue + (lead_total_revenue * 18) / 100
							lead_total_per_day_amount = total_month_revenue_with_gstAmount / 30
							lead_total_five_day_amount = lead_total_per_day_amount * 5
							refundable_amount_to_client = balance_refundable_amount - lead_total_five_day_amount
							
							lead_end_date = None
							
							if lead_total_per_day_amount != 0:									
								num_days_positive = refundable_amount_to_client / lead_total_per_day_amount
								# billing_start_date = frappe.utils.get_first_day(frappe.utils.add_months(today, 1)) if lead_doc.date_of_sales_invoice == '01' or lead_doc.date_of_sales_invoice == '21' else (
								# 	frappe.utils.get_first_day(today) if lead_doc.date_of_sales_invoice == '28' and today < frappe.utils.get_last_day(today) else
								# 	frappe.utils.get_first_day(frappe.utils.add_months(today, 1))
								# )
								if lead_doc.date_of_sales_invoice == '01':
									billing_start_date = frappe.utils.get_first_day(frappe.utils.add_months(today, 1))
								elif lead_doc.date_of_sales_invoice == '21':
									if today.day <= 21:
										billing_start_date = frappe.utils.get_first_day(frappe.utils.add_months(today, 1))
									else:
										billing_start_date = frappe.utils.get_first_day(frappe.utils.add_months(today, 2))
								elif lead_doc.date_of_sales_invoice == '28':
									if today < frappe.utils.get_last_day(today):
										billing_start_date = frappe.utils.get_first_day(today)
									else:
										billing_start_date = frappe.utils.get_first_day(frappe.utils.add_months(today, 1))
								else:
									# Default case if none of the above conditions are met
									billing_start_date = frappe.utils.get_first_day(frappe.utils.add_months(today, 1))

								lead_end_date = frappe.utils.add_days(billing_start_date, num_days_positive)
							if balance_refundable_amount != 0 or payment_entry_deposit != 0 or sales_invoice_deposit != 0 or total_deposit_amount != 0:
								if total_pending_tds_amount != 0 or total_pending_amount != 0:
									if total_deposit_amount != 0 or total_pending_amount != 0 or total_pending_tds_amount >= 0:
										reconciliation_details.append(
											{
												'customer': customer.name,
												'lead_id': lead_string,
												'company':company,
												'deposit_amount': round(total_deposit_amount, 2),
												'pending_tds_amount': round(total_pending_tds_amount, 2),
												"total_pending_amount": round(total_pending_amount, 2),
												'balance_refundable_amount': round(balance_refundable_amount, 2),
												'deposit_in_months': round(deposit_in_months, 2),
												'number_of_seats': number_of_seats,
												'date': lead_end_date
											}
										)
								
				else:
					if balance_refundable_amount != 0 or payment_entry_deposit != 0 or sales_invoice_deposit != 0 or total_deposit_amount != 0:
						if total_pending_tds_amount != 0 or total_pending_amount != 0:
							if total_deposit_amount != 0 or total_pending_amount != 0 or total_pending_tds_amount >= 0:
								reconciliation_details.append(
									{
										'customer': customer.name,
										# 'lead_id': None,
										'company': company,
										'deposit_amount': round(total_deposit_amount, 2),
										'pending_tds_amount': round(total_pending_tds_amount, 2),
										"total_pending_amount": round(total_pending_amount, 2),
										'balance_refundable_amount': round(balance_refundable_amount, 2),
									}
								)
		except Exception as e:
			error_doc = frappe.new_doc('Error log for Scheduler Scripts')
			error_doc.id = f'{customer.name}_{frappe.utils.getdate()}'
			error_doc.customer_name = customer.name
			error_doc.script_name = 'reconciliation_customer_list_scheduler'
			error_doc.error = str(e)
			error_doc.save()
			continue
									
	unique_lead_ids = set()
	# Create a new list to store unique dictionaries
	unique_reconciliation_details = []

	# Iterate through the original list and check for duplicates based on 'lead_id'
	for reconciliation in reconciliation_details:
		try:
			if isinstance(reconciliation, dict):
				lead_id = reconciliation.get('lead_id', None)
			else:
				lead_id = None
			if lead_id:
				if lead_id not in unique_lead_ids:
					unique_lead_ids.add(lead_id)
					unique_reconciliation_details.append(reconciliation)
			else:
				unique_reconciliation_details.append(reconciliation)
		except Exception as e:
			error_doc = frappe.new_doc('Error log for Scheduler Scripts')
			error_doc.id = f'{reconciliation.customer}_{frappe.utils.now()}'
			error_doc.customer_name = reconciliation.customer
			error_doc.script_name = 'reconciliation_customer_list_scheduler'
			error_doc.error = str(e)
			error_doc.save()
			continue

	doc.date = today
	ex_client_doc.date = today
	doc.leasing_status = "Not Ex-Client"
	ex_client_doc.leasing_status = "Ex-Client"

	for reconciliation_row in unique_reconciliation_details:
		# Fetching blocked status from Lead Links
		try:	
			if isinstance(reconciliation_row, dict):
				lead_id = reconciliation_row.get('lead_id', None)
			else:
				lead_id = None
			lead_leasing_status = None
			if lead_id:
				first_lead_id = lead_id.split(',')[0]  # Extracting the first lead ID before the comma
				blocked_lead = frappe.get_all('Lead Links', filters={'parent': first_lead_id}, fields=['blocked'])
				lead_leasing_status = frappe.get_all('Leads', filters={'name': first_lead_id}, fields=['name', 'leasing_status'], limit=1)
				if blocked_lead:
					reconciliation_row['blocked'] = blocked_lead[0]['blocked']
				else:
					reconciliation_row['blocked'] = False
			else:
				reconciliation_row['blocked'] = False

			# Fetching leasing status from Leads
			if lead_leasing_status:
				reconciliation_row['leasing_status'] = lead_leasing_status[0]['leasing_status']
			else:
				reconciliation_row['leasing_status'] = "NA"
			if reconciliation_row['leasing_status'] == "Ex-Client":
				ex_client_doc.append("reconciliation_details", reconciliation_row)
			else:
				doc.append("reconciliation_details", reconciliation_row)
		
		except Exception as e:
			error_doc = frappe.new_doc('Error log for Scheduler Scripts')
			error_doc.id = f'{reconciliation_row.customer}_{frappe.utils.now()}'
			error_doc.customer_name = reconciliation_row.customer
			error_doc.script_name = 'reconciliation_customer_list_scheduler'
			error_doc.error = str(e)
			error_doc.save()
			continue

	doc.save()
	ex_client_doc.save()

	today = frappe.utils.getdate()
	yesterday = frappe.utils.add_to_date(today, days = -1)
	last_reconciliation_customer_list = frappe.get_list("Reconciliation Customer List", 
												filters = {
													'name' : f'{yesterday} - Not Ex-Client',
												},
											)
	if last_reconciliation_customer_list:
		for row in doc.reconciliation_details:
			update_rows = frappe.db.sql(f'''SELECT cr_comments, last_commented_by_cr, ar_comments, last_commented_by_ar FROM `tabReconciliation Customer Details` WHERE parent = "{last_reconciliation_customer_list[0].name}" AND lead_id = "{row.lead_id}"''', as_dict = True)
			if update_rows:
				row.cr_comments = update_rows[0].cr_comments
				row.last_commented_by_cr = update_rows[0].last_commented_by_cr
				row.ar_comments = update_rows[0].ar_comments
				row.last_commented_by_ar = update_rows[0].last_commented_by_ar
		doc.save()

def custom_reconciliation_customer_list_enqueue():
	frappe.enqueue(execute_reconcilitation_customer_list, queue = 'long', timeout=2400)