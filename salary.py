def compute_salary(monthly_wage, pf_rate, professional_tax):
    """
    Takes the monthly wage entered by the admin and works out every
    salary component automatically, following the rules from the
    project requirements:

      Basic Salary          = 50% of wage
      House Rent Allowance  = 50% of Basic
      Standard Allowance    = 16.67% of Basic
      Performance Bonus     = 8.33% of Basic
      Leave Travel Allowance= 8.33% of Basic
      Fixed Allowance       = whatever is left of the wage after
                               the components above are subtracted
      PF (Employee)         = pf_rate% of Basic
      PF (Employer)         = pf_rate% of Basic
      Net Pay               = wage - PF(Employee) - Professional Tax
    """
    wage = float(monthly_wage or 0)
    pf_rate = float(pf_rate or 0)
    professional_tax = float(professional_tax or 0)

    basic = wage * 0.50
    hra = basic * 0.50
    standard_allowance = basic * 0.1667
    performance_bonus = basic * 0.0833
    leave_travel_allowance = basic * 0.0833

    components_so_far = basic + hra + standard_allowance + performance_bonus + leave_travel_allowance
    fixed_allowance = wage - components_so_far
    if fixed_allowance < 0:
        fixed_allowance = 0  # safety net so the UI never shows a negative number

    pf_employee = basic * pf_rate / 100
    pf_employer = basic * pf_rate / 100

    net_pay = wage - pf_employee - professional_tax

    def r(x):
        return round(x, 2)

    return {
        "monthly_wage": r(wage),
        "yearly_wage": r(wage * 12),
        "basic": r(basic),
        "hra": r(hra),
        "standard_allowance": r(standard_allowance),
        "performance_bonus": r(performance_bonus),
        "leave_travel_allowance": r(leave_travel_allowance),
        "fixed_allowance": r(fixed_allowance),
        "pf_rate": r(pf_rate),
        "pf_employee": r(pf_employee),
        "pf_employer": r(pf_employer),
        "professional_tax": r(professional_tax),
        "net_pay": r(net_pay),
    }