import frappe

def one_day_after_on_hold():
    today = frappe.utils.getdate()
    one_days_before = frappe.utils.add_days(today, -1)
    candidates = frappe.get_all('Candidates', filters={'result1': 'On Hold',"last_on_hold_date":one_days_before}, fields=['name','primary_email','last_on_hold_date'])
    for candidate in candidates:
        try:
            last_hold_date = candidate.get('last_on_hold_date')
            primary_email = candidate.get('primary_email')
            
            if last_hold_date == one_days_before and primary_email:
                frappe.sendmail(
                    recipients=primary_email,
                    # bcc= "jatin.k@noveloffice.in",
                    sender="results@noveloffice.in",
                    subject="Interview Results - Novel Office",
                    message = f"Dear Candidate,<br><br>Greetings !!!<br><br>Thank you for your application with Novel Office. We really appreciate your interest in joining our company and we want to thank you for the time and energy you invested in attending/applying for our job opening.<br><br>Though the recruitment process is on, due to some administrative reasons, we have kept your profile on hold and we are uncertain about your candidatures’ logical conclusion.<br><br>I reiterate my appreciation for showing your interest in working with us.<br><br>",
                    expose_recipients="header",
                    now=True,
                )
            success_doc = frappe.new_doc('Success log for Scheduler  Scripts')
            success_doc.id = f'{primary_email}_{frappe.utils.now()}'
            # success_doc.customer_name = primary_email
            success_doc.script_name = 'Rejection mail to candidates 1 days after updating result as On Hold'
            success_doc.save()  
        except Exception as e:
            error_doc = frappe.new_doc('Error log for Scheduler Scripts')
            error_doc.id = f'{primary_email}_{frappe.utils.now()}'
            # error_doc.customer_name = primary_email
            error_doc.script_name = 'Rejection mail to candidates 1 days after updating result as On Hold'
            error_doc.error = str(e)
            error_doc.save()

def one_day_after_on_hold_enqueue():
    frappe.enqueue(one_day_after_on_hold, queue = 'long')