import frappe

def execute_customer_refundable_deposit():
	today = frappe.utils.getdate()
	doc = frappe.new_doc("Customer Refundable Deposit")
	doc.date = today

	customer_refundable_deposit_details = []

	customer_list = frappe.db.sql("""
		SELECT 
			UNIQUE c.name
		FROM 
			`tabCustomer` c
		LEFT JOIN 
			`tabLeads` l 
		ON 
			c.name = l.customer_name
		WHERE 
			(c.location NOT IN ('PROJECTS', 'LOGISTICS') OR c.location IS NULL)
			AND c.name NOT IN (SELECT name FROM `tabCompany`)
			AND (l.leasing_status IS NULL OR l.leasing_status NOT IN ('Ex-Client', 'On Notice'))
	""", as_dict=True)

	for customer in customer_list: 
		# try:       
			customer_name = customer['name']
			
			journal_entry_list = frappe.db.sql(f'''SELECT je.name, je.company, 
											SUM(jea.credit) - SUM(jea.debit) AS balance
											FROM `tabJournal Entry Account` AS jea
											INNER JOIN `tabJournal Entry` AS je
											ON jea.parent = je.name
											WHERE je.docstatus = 1
											AND jea.account LIKE 'Customer Refundable Deposit%'
											AND jea.party = "{customer_name}"
											GROUP BY je.name, je.company''', as_dict=True)
											
			deposit_payment_entry_list = frappe.db.sql(f'''SELECT pe.name, pe.company,
													pd.amount
												FROM `tabPayment Entry` AS pe
												INNER JOIN `tabPayment Entry Deduction` AS pd
												ON pe.name = pd.parent
												WHERE pe.party = "{customer_name}"
												AND pe.docstatus = 1
												AND pd.account LIKE '%Customer Refundable Deposit%'
												''', as_dict=True)
			
			company_list = set()                
			
			for entry in journal_entry_list:
				company_list.add(entry['company'])
			
			for entry in deposit_payment_entry_list:
				company_list.add(entry['company'])
				
			for company in company_list:
				total_deposit_amount = 0
				total_deposit_paid_amount = 0
				deposit_in_leads = 0
				lead_id = ''
				# Calculate deposit for the company from journal_entry_list
				for entry in journal_entry_list:
					if entry['company'] == company:
						total_deposit_amount = total_deposit_amount + entry['balance']
						journal_entry = frappe.db.sql(f'''SELECT jea.name, jea.debit, jea.parent, jea.party, jea.account 
														FROM `tabJournal Entry Account` AS jea
														INNER JOIN `tabJournal Entry` AS je ON jea.parent = je.name
														WHERE je.company = "{entry.company}"
														AND jea.parent = "{entry.name}"
														AND jea.party = "{customer_name}"
														AND jea.account LIKE "Accounts Receivable (Debtors)%"''', as_dict=True)
														
						if journal_entry:
							for jea in journal_entry:
								payment_entry = frappe.db.sql(f'''SELECT per.allocated_amount
																FROM `tabPayment Entry` AS pe
																INNER JOIN `tabPayment Entry Reference` AS per
																ON pe.name = per.parent
																WHERE pe.party = "{customer_name}"
																AND pe.docstatus = 1
																AND pe.company = "{entry.company}"
																AND per.reference_name = "{entry.name}"
																''', as_dict=True)

								for per in payment_entry:
									total_deposit_paid_amount = total_deposit_paid_amount + per['allocated_amount']
						else:
							total_deposit_paid_amount = total_deposit_paid_amount + entry['balance']

				for entry in deposit_payment_entry_list:
					if entry['company'] == company:
						total_deposit_amount = total_deposit_amount - entry['amount']
						total_deposit_paid_amount = total_deposit_paid_amount - entry['amount']

				company_location_dict = {
					"POLISETTY SOMASUNDARAM" : ["NTP"],
					"VIBGYOR NET CONNECTIONS" : ["NOC"],
					"Millertech Spaces LLP" : ["BTP3F", "NOM"],
					"Estetic Spaces LLP (formerly known as 'Novel Office Centre LLP')" : ["BTP1F", "NOQ", "NBP"],
					"Novel Triton LLP" : ["NBP"],
					"Civana Spaces LLP (formerly known as 'Novel Cassini LLP')" : ["NOW"],
				}
				
				confirmed_location = company_location_dict.get(company, None)
				
				if confirmed_location:
					confirmed_location_str = ', '.join(f'"{loc}"' for loc in confirmed_location)
					# Use the IN clause in the SQL query
					lead_query = f'''SELECT name 
										FROM `tabLeads`
										WHERE confirmed_location IN ({confirmed_location_str})
										AND customer_name = "{customer.name}"'''

					lead = frappe.db.sql(lead_query, as_dict=True)

					if lead:
						lead_id = lead[0]['name']

						leads_deposit = frappe.db.sql(f'''
							SELECT
								l.name AS lead_name,
								l.deposit,
								l.customer_name,
								etr.entity,
								etr.refundable_deposit
							FROM
								`tabLeads` AS l
							LEFT JOIN
								`tabEntity Total Revenue` AS etr
							ON
								l.name = etr.parent
							WHERE
								(l.customer_name IS NOT NULL
								OR l.customer_name != "")
							AND
								(l.leasing_status != "Ex-Client")
							AND 
								l.name = "{lead[0]['name']}"
							AND 
								etr.entity = "{company}";
							''', as_dict = True)

						if leads_deposit:
							deposit_in_leads = leads_deposit[0]['refundable_deposit']

				actual_leads_difference_amount = total_deposit_amount - deposit_in_leads
				
				difference_amount = total_deposit_amount - total_deposit_paid_amount

						
				customer_refundable_deposit_details.append(
					{
						'customer': customer_name,
						'company': company,
						'actual_deposit': round(total_deposit_amount, 2),
						'deposit_paid': round(total_deposit_paid_amount, 2),
						# 'deposit_in_leads': round(deposit_in_leads, 2),
						"difference_amount": round(difference_amount, 2),
						"lead_id": lead_id
						# "actual_leads_difference_amount": round(actual_leads_difference_amount, 2),
					}
				)

		# except Exception as e:
		# 	error_doc = frappe.new_doc('Error log for Scheduler Scripts')
		# 	error_doc.id = f'Customer Refundable Deposit - {customer["name"]}'
		# 	error_doc.customer_name = customer['name']
		# 	error_doc.script_name = 'customer_refundable_deposit'
		# 	error_doc.error = str(e)
		# 	error_doc.save()
		# 	continue
				   
	for customer_refundable_deposit in customer_refundable_deposit_details:
		doc.append("customer_refundable_deposit_details", customer_refundable_deposit)
	doc.save()

	today = frappe.utils.getdate()
	yesterday = frappe.utils.add_to_date(today, days = -1)
	last_customer_refundable_deposit = frappe.get_list("Customer Refundable Deposit", 
												filters = {
													'name' : f'{yesterday}',
												},
											)
	if last_customer_refundable_deposit:
		for row in doc.customer_refundable_deposit_details:
			update_comments = frappe.db.sql(f'''SELECT comment FROM `tabCustomer Refundable Deposit Child Table` WHERE parent = "{last_customer_refundable_deposit[0].name}" AND customer = "{row.customer}" AND company = "{row.company}"''', as_dict = True)
			if update_comments:
				row.comment = update_comments[0].comment
		doc.save()

def custom_customer_refundable_deposit_enqueue():
	frappe.enqueue(execute_customer_refundable_deposit, queue = 'long')


#     today = frappe.utils.getdate()
#     doc = frappe.new_doc("Customer Refundable Deposit")

#     customer_refundable_deposit_details = []

#     # exempt_customer_list = ["M. Sarasa", "S Vinod Reddy", "S Pramod Reddy", "M Shama Reddy", "Suspense Account (C)", "HDFC Bank Limited", "Pramila Elecon", "Hassan Gowdaiah Sukanya", "Bedegere Sudhanva Sidharth"]
#     # exempt_customer_string = ', '.join(['%s' for i in exempt_customer_list])

#     customer_list = frappe.db.sql(f"""
#         SELECT name 
#         FROM `tabCustomer` 
#         WHERE (location NOT IN ('PROJECTS', 'LOGISTICS') OR location IS NULL)
#         AND name NOT IN (SELECT name FROM `tabCompany`)
#     """, as_dict=True)

#     for customer in customer_list:
		
#         lead_leasing_status = frappe.db.sql(f'''SELECT name, leasing_status FROM `tabLeads` WHERE customer_name = "{customer.name}"''', as_dict = True)
		
#         for lead in lead_leasing_status:
#             if leasing_status[leasing_status] not in ["Ex-Client", "On Notice"]:

			
#             customer_name = customer['name']
			
#             journal_entry_list = frappe.db.sql(f'''SELECT je.name, je.company, 
#                                             SUM(jea.credit) - SUM(jea.debit) AS balance
#                                             FROM `tabJournal Entry Account` AS jea
#                                             INNER JOIN `tabJournal Entry` AS je
#                                             ON jea.parent = je.name
#                                             WHERE je.docstatus = 1
#                                             AND jea.account LIKE 'Customer Refundable Deposit%'
#                                             AND jea.party = "{customer_name}"
#                                             GROUP BY je.name, je.company''', as_dict=True)
											
#             deposit_payment_entry_list = frappe.db.sql(f'''SELECT pe.name, pe.company,
#                                                     pd.amount
#                                                 FROM `tabPayment Entry` AS pe
#                                                 INNER JOIN `tabPayment Entry Deduction` AS pd
#                                                 ON pe.name = pd.parent
#                                                 WHERE pe.party = "{customer_name}"
#                                                 AND pe.docstatus = 1
#                                                 AND pd.account LIKE '%Customer Refundable Deposit%'
#                                                 ''', as_dict=True)
			
#             company_list = set()                
			
#             for entry in journal_entry_list:
#                 company_list.add(entry['company'])
			
#             for entry in deposit_payment_entry_list:
#                 company_list.add(entry['company'])
				
#             for company in company_list:
#                 total_deposit_amount = 0
#                 total_deposit_paid_amount = 0
#                 # Calculate deposit for the company from journal_entry_list
#                 for entry in journal_entry_list:
#                     # log(entry)
#                     if entry['company'] == company:
#                         total_deposit_amount = total_deposit_amount + entry['balance']
#                         journal_entry = frappe.db.sql(f'''SELECT jea.name, jea.debit, jea.parent, jea.party, jea.account 
#                                                         FROM `tabJournal Entry Account` AS jea
#                                                         INNER JOIN `tabJournal Entry` AS je ON jea.parent = je.name
#                                                         WHERE je.company = "{entry.company}"
#                                                         AND jea.parent = "{entry.name}"
#                                                         AND jea.party = "{customer_name}"
#                                                         AND jea.account LIKE "Accounts Receivable (Debtors)%"''', as_dict=True)
														
#                         # log(journal_entry)
#                         if journal_entry:
#                             for jea in journal_entry:
#                                 payment_entry = frappe.db.sql(f'''SELECT per.allocated_amount
#                                                                 FROM `tabPayment Entry` AS pe
#                                                                 INNER JOIN `tabPayment Entry Reference` AS per
#                                                                 ON pe.name = per.parent
#                                                                 WHERE pe.party = "{customer_name}"
#                                                                 AND pe.docstatus = 1
#                                                                 AND pe.company = "{entry.company}"
#                                                                 AND per.reference_name = "{entry.name}"
#                                                                 ''', as_dict=True)
#                                 # log(payment_entry)
#                                 for per in payment_entry:
#                                     total_deposit_paid_amount = total_deposit_paid_amount + per['allocated_amount']
#                         else:
#                             total_deposit_paid_amount = total_deposit_paid_amount + entry['balance']
						
#                 #     log("\n")
#                 # log(total_deposit_amount)
#                 # log(total_deposit_paid_amount)
#                 # log(total_deposit_amount - total_deposit_paid_amount)
#                 for entry in deposit_payment_entry_list:
#                     if entry['company'] == company:
#                         total_deposit_amount = total_deposit_amount - entry['amount']
#                         total_deposit_paid_amount = total_deposit_paid_amount - entry['amount']
				
#                 difference_amount = total_deposit_amount - total_deposit_paid_amount
						
#                 customer_refundable_deposit_details.append(
#                     {
#                         'customer': customer_name,
#                         'company': company,
#                         'actual_deposit': round(total_deposit_amount, 2),
#                         'deposit_paid': round(total_deposit_paid_amount, 2),
#                         "difference_amount": round(difference_amount, 2),
#                     }
#                 )
						
#         doc.date = today
#         for customer_refundable_deposit in customer_refundable_deposit_details:
#             doc.append("customer_refundable_deposit_details", customer_refundable_deposit)
#         doc.save()

# def custom_customer_refundable_deposit_enqueue():
# 	frappe.enqueue(execute_customer_refundable_deposit, queue = 'long')
