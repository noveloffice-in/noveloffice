import frappe

def one_day_after():
    today = frappe.utils.getdate()
    one_days_before = frappe.utils.add_days(today, -1)
    candidates = frappe.get_all('Candidates', filters={'application_status': 'Rejected', 'date_of_calling': one_days_before}, fields=['name','primary_email','date_of_calling'])
    for candidate in candidates:
        try:
            date_of_call = candidate.date_of_calling
            primary_email = candidate.primary_email
            
            if primary_email:
                frappe.sendmail(
                    recipients=primary_email,
                    # bcc= "jatin.k@noveloffice.in",
                    sender="results@noveloffice.in",
                    subject="Novel Office",
                    message=f"""Dear Candidate,<br><br>We value your interest in Novel Office and sincerely appreciate the time and effort you put into applying with us. After careful consideration of your application, we regret to inform you that your profile is not shortlisted for further rounds.<br><br>Best of luck for future endeavours.<br><br>""",
                    expose_recipients="header",
                    now=True,
                )
        except Exception as e:
            frappe.msgprint(e)

def one_day_after_enqueue():
    frappe.enqueue(one_day_after, queue = 'long')