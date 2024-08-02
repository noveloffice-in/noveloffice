import frappe

def two_days_updating_future_hire():
    today = frappe.utils.getdate()
    two_days_before = frappe.utils.add_days(today, -2)
    candidates = frappe.get_all('Candidates', filters={'result1': 'Future Hire',"last_future_hire_date" :two_days_before}, fields=['name','primary_email','last_future_hire_date'])
    for candidate in candidates:
        try:
            last_rejected_date = candidate.get('last_future_hire_date')
            primary_email = candidate.get('primary_email')
            
            if last_rejected_date == two_days_before and primary_email:
                frappe.sendmail(
                    recipients=primary_email,
                    # bcc= "jatin.k@noveloffice.in",
                    sender="results@noveloffice.in",
                    subject="Interview Results - Novel Office",
                    message=f"""Dear Candidate,<br> Greetings from Novel Office!<br><br>Thank you for attending the interview with Novel Office. It was a pleasure to learn more about your skills and accomplishments. We regret to inform you that our team did not shortlist your profile for further consideration. We would like to note here that competition for jobs at Novel Office is always strong, and we often have to make difficult choices between many high-calibre candidates. Now that we’ve had the chance to know more about you, we will be keeping your resume on file for future openings that better fit your profile.<br><br>We would greatly appreciate it if you could take a moment to provide feedback on our interview process by completing this form. Your feedback will help us improve our processes and ensure a better experience for all candidates.<br><br>https://forms.gle/eokxtVBLuf9QWewc8<br><br>Thanks again for your interest in Novel Office, and best of luck for your future professional endeavours.<br><br>""",
                    expose_recipients="header",
                    now=True,
                )
                success_doc = frappe.new_doc('Success log for Scheduler  Scripts')
                success_doc.id = f'{primary_email}_{frappe.utils.now()}'
                # success_doc.customer_name = primary_email
                success_doc.script_name = 'Rejection mail to candidates 2 days after updating result Future Hire'
                success_doc.save()  
        except Exception as e:
            error_doc = frappe.new_doc('Error log for Scheduler Scripts')
            error_doc.id = f'{primary_email}_{frappe.utils.now()}'
            error_doc.customer_name = primary_email
            error_doc.script_name = 'Rejection mail to candidates 2 days after updating result Future Hire'
            error_doc.error = str(e)
            error_doc.save()

def two_days_updating_future_hire_enqueue():
    frappe.enqueue(two_days_updating_future_hire, queue = 'long')