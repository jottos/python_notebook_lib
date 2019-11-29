# -*- coding: utf-8 -*-
from typing import List, Set, Dict, Tuple, Optional, ClassVar
from dateutil.parser import parse as parse_date
from datetime import datetime

__version__ = "0.1.0"
__all__ = ['create_hive_date_range_filter']

"""
python 3.4? and above - uses types and "f" strings


test_cases = [("10/1/2019", "10/1/2019"),("10/22/2019", "10/30/2019"), ("10/22/2019", "11/4/2019"),("1/1/2019", "3/4/2019"),("2/10/2019", "3/4/2019"),("10/22/2019", "11/4/2020"),("10/22/2017", "11/4/2020")]

for test in test_cases:
    print(f"TEST {test}")
    print(create_hive_date_range_filter(*test))
    print()


TEST ('10/1/2019', '10/1/2019')
((year = '2019' and month = '10' and days in ('01')))

TEST ('10/22/2019', '10/30/2019')
((year = '2019' and month = '10' and days in ('22', '23', '24', '25', '26', '27', '28', '29', '30')))

TEST ('10/22/2019', '11/4/2019')
((year = '2019' and month = '10' and days in ('22', '23', '24', '25', '26', '27', '28', '29', '30', '31'))
  or (year = '2019' and month = '11' and days in ('01', '02', '03', '04')))

TEST ('1/1/2019', '3/4/2019')
((year = '2019' and month in ('01', '02')
  or (year = '2019' and month = '03' and days in ('01', '02', '03', '04')))

TEST ('2/10/2019', '3/4/2019')
((year = '2019' and month = '02' and days in ('10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28'))
  or (year = '2019' and month = '03' and days in ('01', '02', '03', '04')))

TEST ('10/22/2019', '11/4/2020')
((year = '2019' and month = '10' and days in ('22', '23', '24', '25', '26', '27', '28', '29', '30', '31'))
  or (year = '2019' and month in ('11', '12')
  or (year = '2020' and month in ('01', '02', '03', '04', '05', '06', '07', '08', '09', '10')
  or (year = '2020' and month = '11' and days in ('01', '02', '03', '04')))

TEST ('10/22/2017', '11/4/2020')
((year = '2017' and month = '10' and days in ('22', '23', '24', '25', '26', '27', '28', '29', '30', '31'))
  or (year = '2017' and month in ('11', '12')
  or (year = '2018')
  or (year = '2019')
  or (year = '2020' and month in ('01', '02', '03', '04', '05', '06', '07', '08', '09', '10')
  or (year = '2020' and month = '11' and days in ('01', '02', '03', '04')))
"""

def create_hive_date_range_filter(start_date:str, end_date:str) -> str:
    """
    create a hive filter for a date range at the day level
    cases are
    1) all in one month
    2) span a single month boundary
    3) span multiple month boundaries
    4) span a month boundary over a year boundary
    5) span multiple month boundaries where one is a year boundary
    6) span multiple year bounaries
    """
    if parse_date(end_date) < parse_date(start_date):
        raise Exception(f"create_hive_date_range: illegal date range {start_date}, {end_date}")
    
    days_in_month = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 
                     7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
    def get_days_in_month(date:datetime, days:str) -> List[str]:
        """
        date - date with month from which to get days for, days are returned as a list of strings
          representing the days numerically. eg. '01'
        upto_days - if 'from_beginning', then return from beginning of month '01' upto and including the day, 
          if 'to_end' then return from from that day to end of month 
          
        see days_in_month map for the lenght of each month

        TODO: jos, need dynamic update for leap years
        """
        day = int(date.day)
        if days == 'from_beginning':
            return [day for day in range(1, day + 1)]
        elif days == 'to_end':
            return [day for day in range(day, days_in_month[date.month] + 1)]
        else:
            raise Exception("upto_days must be either 'from_beginning' or 'to_end'")


    def is_last_day_in_month(date:datetime) -> bool:
        return date.day == days_in_month[date.month]

    
    def get_days_between_two_days(start_day:int, end_day:int):
        if start_day < 1 or end_day > 31:
            # this is not exact, if it were, we'd take the month and check the end date
            raise Exception("start_day or end_day out of range")
        return [day for day in range(start_day, end_day + 1)]


    def generate_clause(year:int, months:List[int], days:List[int]) -> str:
        """
        Generate a clause given a year, list of months and list of days
         * days and months may be None
         * otherwise months may be 1 or more ints representing months in year eg. 1 to 12
         * days may be 1 or more ints representing days, eg. 1 to '31'
        
        the allowable combinations are:
          * year None None -> (year = 'some year')
          * year card(months) == 1 None -> (year = 'some year' and month in ('a month'))
          * year card(months) > 1 None  -> (year = 'some year' and month in ('month', 'month'))
          * year card(months) == 1 days -> (year = 'some year' and month = month and days in ('day', 'day'))
        
        year card(months) > 1 card(days) > 1 -> raise Exception("Illegal parameters")
        """
        # these just make it clear that there are no days or months
        if days == []:
            days = None
        if months == []:
            months = None
        
        day_clause = f" and days in ({str([f'{d:02}' for d in days])[1:-1]})" if days else ""
        if months and len(months) > 1:
            if days:
                raise Exception("generate_clause: illegal clause parameters")
            else:
                return  f"(year = '{year:02}' and month in ({str([f'{m:02}' for m in months])[1:-1]})"
        else:
            month_clause = f" and month = {str([f'{m:02}' for m in months])[1:-1]}" if months and len(months) == 1 else ""

        if month_clause == "" and day_clause != "":
            raise Exception("generate_clause: illegal clause parameters")

        return f"(year = '{year:02}'{month_clause}{day_clause})"

    sd = parse_date(start_date)
    ed = parse_date(end_date)        
    clauses = []
    accumulated_months = []
    for year in range(sd.year, ed.year + 1):
        in_first_year = True if year == sd.year else False
        in_last_year = True if year == ed.year else False

        if year > sd.year and year < ed.year:
            # emit a year only clause
            clauses.append(generate_clause(year, accumulated_months , days))
        else:
            # collect or emit a first, last or only month
            first_month = sd.month if in_first_year else 1
            last_month = ed.month if in_last_year else 12            
            for month in range(first_month, last_month + 1):
                days = None
                if sd.year == ed.year and first_month == last_month:
                    # all days of entire range are in the same month
                    days = get_days_between_two_days(sd.day, ed.day)
                elif in_first_year and month == first_month:
                    # this is the first month in series, get days from date to end of that month
                    if sd.day == 1:
                        # if this first month starts with day one, just add the entire month
                        accumulated_months.append(month)
                    else:
                        days = get_days_in_month(sd, 'to_end')
                elif in_last_year and month == last_month:
                    # this is the last month in the series, get the days from 1st of month till last day
                    if is_last_day_in_month(ed):
                        # if last days is last day in month, add entire month
                        acumulated_months.append(month)
                    else:
                        days = get_days_in_month(ed, 'from_beginning')
                else:
                    # no days needed, whole month
                    days = None
                    accumulated_months.append(month)

                if month == last_month and len(accumulated_months) > 0:
                    # we reached end of first year boundary and need to emit any accumulated months
                    clauses.append(generate_clause(year, accumulated_months, None))
                    accumulated_months = []

                if days:
                    #generate a full year, month, days clause for what is either the first or last month
                    clauses.append(generate_clause(year, [month], days))

    or_str = '\n  or '
    return f"({or_str.join(clauses)})"

