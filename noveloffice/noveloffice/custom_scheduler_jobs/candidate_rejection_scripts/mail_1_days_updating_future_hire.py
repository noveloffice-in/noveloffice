import frappe

def one_day_after_updating_future_hire():
    today = frappe.utils.getdate()
    one_days_before = frappe.utils.add_days(today, -1)
    candidates = frappe.get_all('Candidates', filters={'application_status': 'Future Hire',"date_of_calling":one_days_before}, fields=['name','primary_email','date_of_calling'])
    for candidate in candidates:
        try:
            date_of_call = candidate.get('date_of_calling')
            primary_email = candidate.get('primary_email')
            
            if date_of_call == one_days_before and primary_email:
                frappe.sendmail(
                    recipients=primary_email,
                    # bcc= "jatin.k@noveloffice.in",
                    sender="results@noveloffice.in",
                    subject="Novel Office",
                    message=f"""Dear Candidate,<br><br>We value your interest in Novel Office and sincerely appreciate the time and effort you put into applying with us. After careful consideration of your application, we regret to inform you that your profile is not shortlisted for further rounds.<br><br>Best of luck for future endeavours.<br><br>""",
                    expose_recipients="header",
                    now=True,
                )
            success_doc = frappe.new_doc('Success log for Scheduler  Scripts')
            success_doc.id = f'{primary_email}_{frappe.utils.now()}'
            # success_doc.customer_name = primary_email
            success_doc.script_name = 'Rejection mail to candidates 1 days after updating appllication status Future Hire'
            success_doc.save()  
        except Exception as e:
            error_doc = frappe.new_doc('Error log for Scheduler Scripts')
            error_doc.id = f'{primary_email}_{frappe.utils.now()}'
            # error_doc.customer_name = primary_email
            error_doc.script_name = 'Rejection mail to candidates 1 days after updating appllication status Future Hire'
            error_doc.error = str(e)
            error_doc.save()

def one_day_updating_status_future_hire_enqueue():
    frappe.enqueue(one_day_after_updating_future_hire, queue = 'long')