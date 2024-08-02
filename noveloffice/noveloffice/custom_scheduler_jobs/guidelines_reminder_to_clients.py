import frappe

def guidelines_reminder_to_clients():
	all_customer = frappe.db.sql("SELECT DISTINCT(customer_name) FROM `tabLeads` WHERE leasing_status != 'Ex-Client' AND customer_name IS NOT NULL ORDER BY customer_name;")

	for cust in all_customer:
		try:
			email = frappe.db.sql('SELECT email FROM tabEmail_list_invoice where parent = "%s"' %cust[0])
			recipients = list([item[0] for item in email if item[0]!= None])
			subject = "Enhancements and Guidelines for an Optimal Workspace Experience at Novel Office"
			message = f'''Dear Valued Clients,
			<br><br>
			We hope this email finds you in high spirits and enjoying your time at Novel Office - Best co-working and managed office spaces. As part of our ongoing commitment to providing you with the best experience, we would like to share some important updates and guidelines to ensure a smooth and enjoyable work environment for everyone.
			<br><br>
			<b><u>Gate-Pass:</b></u> To ensure the security of your valuable assets and to streamline the movement of assets outside the building, we kindly request that you inform our team at least 1 working day in advance. This advance notice enables us to make the necessary arrangements and provide you with the required gate-passes promptly.
			<br><br>
			<b><u>QR Stickers:</b></u> In our continuous efforts to enhance security measures, we have implemented a mandatory QR sticker policy for all vehicles accessing our premises. These stickers facilitate smooth entry and exit procedures while maintaining a secure environment for all. We kindly request your cooperation in diligently handling/carrying the QR stickers to enter premises.
			<br><br>
			<b><u>No Tailgating:</b></u> Kindly adhere to the no tailgating policy while entering the premises. This ensures the security and safety of all occupants.
			<br><br>
			<b><u>Food consumption in office space:</b></u> Maintaining a clean and hygienic workspace is essential for the well-being of all occupants. In consideration of this, we kindly request that food consumption and any cake cutting be limited to designated areas i.e., Cafeteria. This measure helps us prevent the presence of pests and rodents, ensuring a pleasant and healthy workspace for everyone.
			<br><br>
			<b><u>Usage of UPS Sockets:</b></u> To maintain a stable and efficient electrical system, we kindly request that UPS sockets be used exclusively for essential equipment such as computers and office devices. Connecting printers and servers to these sockets may compromise the system's performance. By adhering to this guideline, we can ensure a reliable power supply for all occupants.
			<br><br>
			<b><u>Annual Power Shutdown:</b></u> Please note that there will be an annual power shutdown due to building maintenance. We will inform you in advance about the specific dates to minimize any inconvenience.
			<br><br>
			<b><u>Tissue Usage:</b></u> Kindly refrain from taking tissues from the washrooms to the office space. This helps ensure that washroom facilities always remain well-stocked and hygienic.
			<br><br>
			<b><u>Smoking Area Etiquette:</b></u> Please use the provided ashtrays for properly disposing of cigarette butts in the designated smoking area. This ensures a clean and tidy environment for all.
			<br><br>
			<b><u>Mobile Phone Usage:</b></u> For the convenience and consideration of all occupants, we kindly request that mobile phone usage be kept to a minimum in common passages to avoid disturbances.
			<br><br>
			<b><u>Assets and Personal belongings:</b></u> Kindly note that Novel will not be held liable for any loss or damage to your belongings. We encourage you to take the necessary precautions to ensure the safety of your assets.
			<br><br>
			<b><u>Shutdown the Computer:</b></u> Optimize energy usage and system efficiency by shutting down your computer before leaving for the day
			
			<br><br>
			
			
			We greatly appreciate your understanding, support, and adherence to these guidelines. Our aim is to create a vibrant and conducive work environment where you can thrive professionally. Should you have any queries or require further assistance, please feel free to reach out to our dedicated Client Relation team. We are here to assist you in any way we can.
			<br><br>
			Thank you for choosing Novel Office as your workspace provider. We value your presence and look forward to continuing our partnership to create productive and inspiring workspaces
			<br><br>
			'''

			frappe.sendmail(
				sender = "erpnextalert@noveloffice.in",
				recipients = recipients,
				# recipients = ["aditya.n@noveloffice.in"],
				bcc = ["aditya.n@noveloffice.in"],
				subject=subject,
				message=message,
				now=True,
				expose_recipients = "header"
				)    
			success_doc = frappe.new_doc('Success log for Scheduler  Scripts')
			success_doc.id = f'{cust}_{frappe.utils.now()}'
			success_doc.customer_name = cust
			success_doc.script_name = 'guideline_reminder_to_clients'
			success_doc.save()
			
		except Exception as e:
			error_doc = frappe.new_doc('Error log for Scheduler Scripts')
			error_doc.id = f'{cust}_{frappe.utils.now()}'
			error_doc.customer_name = cust
			error_doc.script_name = 'guideline_reminder_to_clients'
			error_doc.error = str(e)
			error_doc.save()
			continue

def guidelines_reminder_to_clients_enqueue():
	frappe.enqueue(guidelines_reminder_to_clients, queue = 'long')