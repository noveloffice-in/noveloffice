import frappe

def total_revenue_and_refundable_deposit():
    current_year = frappe.utils.getdate().year
    current_month = frappe.utils.getdate().month
    current_date = frappe.utils.getdate()
    current_day = frappe.utils.getdate().day

    lead = frappe.db.get_list('Leads', pluck = 'name',
                                filters = {
                                    'leasing_status': ['in', ['Client', 'On Notice', 'Deposit Received','Token Received']]
                                })
    
    product_names = frappe.get_list('Leads Items for number of seats', pluck = 'name')
    c = 0

    for lea in lead:
        c = c + 1
        list1 = []
        list2 = []
        list3 = []
        if lea:
            try:
                total_revenue = 0
                refund_deposit = 0
                total_seats = 0
                doc = frappe.get_doc('Leads', lea)
                entity_refundable_dep = {}
                entity_total_rev = {}
                entity_total_seats = {}
                doc.set('entity_refundable_deposit', [])
                doc.set('entity_total_revenue', [])
                for item in doc.item:
                    key = item.novel_billing_entity
                    start_date = item.start_date
                    start_year = start_date.year
                    start_month = start_date.month
                    start_day = start_date.day
                    stop_date = item.stop_date
                    stop_year = stop_date.year
                    stop_month = stop_date.month
                    stop_day = stop_date.day
                    prorated_rate = item.rate
                    num_days = frappe.utils.get_last_day(current_date).day
                    #Total Revenue Calculation
                    if item.item_code == 'Excess Deposit':
                        continue
                    else:
                        start_condition = (start_year, start_month, start_day) <= (current_year, current_month, current_day)
                        stop_condition = (stop_year, stop_month, stop_day) >= (current_year, current_month, current_day)
                        if start_condition and stop_condition:
                            if current_month == start_month and current_month == stop_month and stop_year == current_year and start_year == current_year:
                                prorated_rate = (((stop_day - start_day)+1)/num_days)*prorated_rate
                                
                            elif current_month == start_month and start_year == current_year:
                                prorated_rate = (((num_days - start_day)+1)/num_days)*prorated_rate
                                
                            elif current_month == stop_month and current_year == stop_year:
                                prorated_rate = (stop_day/num_days)*prorated_rate
                                
                            
                            amount = item.qty * prorated_rate
                            if key not in entity_total_rev:
                                entity_total_rev[key] = 0
                            entity_total_rev[key] = entity_total_rev[key] + amount
                            total_revenue = total_revenue + amount   
                    
                    #Refundable deposit calculation
                    if ((current_date >= item.start_date and current_date <= item.stop_date) or (current_date < item.start_date and current_date < item.stop_date)):
                        if key not in entity_refundable_dep:
                            entity_refundable_dep[key] = 0
                        entity_refundable_dep[key] = entity_refundable_dep[key] + item.deposit_amt
                        refund_deposit = refund_deposit + item.deposit_amt
                    if ((current_date > item.start_date and current_date > item.stop_date)  and (item.rollout_status in ('Pre Increment', 'CEF', 'Pre Price Change', 'Pre Movement', 'Pre Name Change'))):
                        if key not in entity_refundable_dep:
                            entity_refundable_dep[key] = 0
                        entity_refundable_dep[key] = entity_refundable_dep[key] + item.deposit_amt
                        
                        refund_deposit = refund_deposit+item.deposit_amt
                    
                    #Total Seats calculation
                    start_condition = (start_year, start_month, start_day) <= (current_year, current_month, current_day)
                    stop_condition = (stop_year, stop_month, stop_day) >= (current_year, current_month, current_day)
                    if start_condition and stop_condition:
                        if item.item_code in product_names:
                            if key not in entity_total_seats:
                                entity_total_seats[key] = 0
                            entity_total_seats[key] = entity_total_seats[key] + item.qty
                            
                            total_seats = total_seats + item.qty    

                for amenity in doc.amenity_recursion:
                    key = amenity.novel_billing_entity
                    start_date = amenity.start_date
                    start_year = start_date.year
                    start_month = start_date.month
                    start_day = start_date.day
                    stop_date = amenity.stop_date
                    stop_year = stop_date.year
                    stop_month = stop_date.month
                    stop_day = stop_date.day
                    prorated_rate = amenity.rate
                    num_days = frappe.utils.get_last_day(current_date).day
                    #Total Revenue Calculation
                    if amenity.item_code == 'Excess Deposit':
                        continue
                    else:
                        start_condition = (start_year, start_month, start_day) <= (current_year, current_month, current_day)
                        stop_condition = (stop_year, stop_month, stop_day) >= (current_year, current_month, current_day)
                        if start_condition and stop_condition:
                            if current_month == start_month and current_month == stop_month and stop_year == current_year and start_year == current_year:
                                prorated_rate = (((stop_day - start_day)+1)/num_days)*prorated_rate
                                
                            elif current_month == start_month and start_year == current_year:
                                prorated_rate = (((num_days - start_day)+1)/num_days)*prorated_rate
                                
                            elif current_month == stop_month and current_year == stop_year:
                                prorated_rate = (stop_day/num_days)*prorated_rate
                                
                            
                            amount = amenity.qty * prorated_rate
                            if key not in entity_total_rev:
                                entity_total_rev[key] = 0
                            entity_total_rev[key] = entity_total_rev[key] + amount
                            total_revenue = total_revenue + amount
                    
                    #Refundable deposit calculation
                    if ((current_date >= amenity.start_date and current_date <= amenity.stop_date) or (current_date < amenity.start_date and current_date < amenity.stop_date)):
                        if key not in entity_refundable_dep:
                            entity_refundable_dep[key] = 0
                        entity_refundable_dep[key] = entity_refundable_dep[key] + amenity.deposit_amt
                        refund_deposit = refund_deposit + amenity.deposit_amt
                    if ((current_date > amenity.start_date and current_date > amenity.stop_date)  and (amenity.rollout_status in ('Pre Increment', 'CEF', 'Pre Price Change', 'Pre Movement', 'Pre Name Change'))):
                        if key not in entity_refundable_dep:
                            entity_refundable_dep[key] = 0
                        entity_refundable_dep[key] = entity_refundable_dep[key] + amenity.deposit_amt
                        
                        refund_deposit = refund_deposit+amenity.deposit_amt
                    
                    #Total Seats calculation
                    start_condition = (start_year, start_month, start_day) <= (current_year, current_month, current_day)
                    stop_condition = (stop_year, stop_month, stop_day) >= (current_year, current_month, current_day)
                    if start_condition and stop_condition:
                        if amenity.item_code in product_names:
                            if key not in entity_total_seats:
                                entity_total_seats[key] = 0
                            entity_total_seats[key] = entity_total_seats[key] + amenity.qty
                            
                            total_seats = total_seats + amenity.qty            
                if entity_refundable_dep or entity_refundable_dep:
                    if (len(entity_refundable_dep) > 0 and len(entity_refundable_dep) > 0):
                        for nbet, rev in entity_total_rev.items():
                            for nbed, dep in entity_refundable_dep.items():
                                if nbet == nbed:
                                    if dep and rev:
                                        list3.append({'entity': nbet,
                                            'refundable_deposit': round(dep,2),
                                            'total_revenue': round(rev,2),
                                        })
                                elif nbet != nbed:
                                    if len(entity_refundable_dep) < len(entity_total_rev):
                                        if nbet:
                                            if rev:
                                                list1.append({
                                                    'entity' : nbet,
                                                    'total_revenue' : round(rev,2)
                                                })
                                    elif len(entity_refundable_dep) > len(entity_total_rev):
                                        if nbed:
                                            if dep:
                                                list2.append({
                                                    'entity' : nbed,
                                                    'refundable_deposit' : round(dep,2)
                                                })
                                    
                    elif (len(entity_refundable_dep) > 0 and len(entity_total_rev) == 0):
                        for nbed, dep in entity_refundable_dep.items():
                            if dep:
                                list2.append({
                                            'entity' : nbed,
                                            'refundable_deposit' : round(dep,2),
                                            'total_revenue' : 0
                                        })
                    
                    elif (len(entity_refundable_dep) == 0 and len(entity_total_rev) > 0):
                        for nbet, rev in entity_total_rev.items():
                            if rev:
                                list1.append({
                                            'entity' : nbet,
                                            'refundable_deposit' : 0,
                                            'total_revenue' : round(rev,2)
                                        })
                    if list3:
                        doc.extend('entity_total_revenue', list3)
                    if list2:
                        doc.extend('entity_total_revenue', list2)
                    if list1:
                        doc.extend('entity_total_revenue', list1)    
                    
                    for item in doc.entity_total_revenue:
                        deposit = item.refundable_deposit
                        deposit = float(deposit if deposit is not None else 0) + float(doc.ed if doc.ed is not None else 0) + float(doc.ed_due_to_downsize if doc.ed_due_to_downsize is not None else 0)
                        item.refundable_deposit = deposit
                        break

                    if len(entity_total_seats) > 0:
                        for nbes, seats in entity_total_seats.items():
                            for item in doc.entity_total_revenue:
                                if nbes == item.entity:
                                    item.no_of_seats = seats 
                    
                    refund_deposit = float(refund_deposit if refund_deposit is not None else 0) + float(doc.ed if doc.ed is not None else 0) + float(doc.ed_due_to_downsize if doc.ed_due_to_downsize is not None else 0)
                    doc.total_revenue = total_revenue
                    doc.deposit = refund_deposit
                    # doc.number_of_seats = total_seats            
                    doc.save()

            except Exception as e:
                error_doc = frappe.new_doc('Error log for Scheduler Scripts')
                error_doc.id = f'{lea}_{frappe.utils.now()}'
                error_doc.lead_name = lea
                error_doc.error = str(e)
                error_doc.script_name = 'Total Revenue And Refundable Deposit Scheduler'
                error_doc.save()
                continue

def total_revenue_and_refundable_deposit_enqueue():
    frappe.enqueue(total_revenue_and_refundable_deposit, queue = 'long')