# -*- coding: utf-8 -*-
from typing import List, Set, Dict, Tuple, Optional, ClassVar
from dateutil.parser import parse as parse_date
from datetime import datetime

__version__ = "0.1.0"
__all__ = ['create_hive_date_range_filter', 'check_file_writable']

"""
requires python 3.4? and above - uses types and "f" strings

you can run the unittests in a Jupyter Notebook with 
> import unittest
> from joslib.dbsupport import TestHiveDateRange
> unittest.main(argv=[''], verbosity=2, exit=False)
"""

def check_file_writable(fnm):
    import os
    if os.path.exists(fnm):
        # path exists
        if os.path.isfile(fnm): # is it a file or a dir?
            # also works when file is a link and the target is writable
            return os.access(fnm, os.W_OK)
        else:
            return False # path is a dir, so cannot write as a file
    # target does not exist, check perms on parent dir
    pdir = os.path.dirname(fnm)
    if not pdir: pdir = '.'
    # target is creatable if parent dir is writable
    return os.access(pdir, os.W_OK)


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
        
        day_clause = f" and day in ({str([f'{d:02}' for d in days])[1:-1]})" if days else ""
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
                        accumulated_months.append(month)
                    else:
                        days = get_days_in_month(ed, 'from_beginning')
                else:
                    # no days needed, whole month
                    days = None
                    accumulated_months.append(month)

                if month == last_month and len(accumulated_months) > 0:
                    # we reached end of first year boundary and need to emit any accumulated months
                    if len(accumulated_months) == 12:
                        #just emit the year
                        clauses.append(generate_clause(year, None, None))
                    else:
                        clauses.append(generate_clause(year, accumulated_months, None))
                    accumulated_months = []

                if days:
                    #generate a full year, month, days clause for what is either the first or last month
                    clauses.append(generate_clause(year, [month], days))

    or_str = '\n  or '
    return f"({or_str.join(clauses)})"


import unittest
class TestHiveDateRange(unittest.TestCase):

    def test_single_day(self):
        self.assertEqual(create_hive_date_range_filter("10/1/2019", "10/1/2019"),
                        """((year = '2019' and month = '10' and day in ('01')))""")

    def test_all_in_one_month(self):
        self.assertEqual(create_hive_date_range_filter("10/22/2019", "10/30/2019"),
                        """((year = '2019' and month = '10' and day in ('22', '23', '24', '25', '26', '27', '28', '29', '30')))""")

    def test_span_one_month_boundary(self):
        self.assertEqual(create_hive_date_range_filter("10/22/2019", "11/4/2019"),
                        """((year = '2019' and month = '10' and day in ('22', '23', '24', '25', '26', '27', '28', '29', '30', '31'))
  or (year = '2019' and month = '11' and day in ('01', '02', '03', '04')))""")
        
    def test_span_one_month_boundary_over_year_boundary(self):
        self.assertEqual(create_hive_date_range_filter("12/25/2019", "1/3/2020"),
                        """((year = '2019' and month = '12' and day in ('25', '26', '27', '28', '29', '30', '31'))
  or (year = '2020' and month = '01' and day in ('01', '02', '03')))""")
        
    def test_span_multiple_months_same_year_start_full_month(self):
        self.assertEqual(create_hive_date_range_filter("1/1/2019", "3/4/2019"),
                        """((year = '2019' and month in ('01', '02')
  or (year = '2019' and month = '03' and day in ('01', '02', '03', '04')))""")

    def test_span_multiple_months_same_year_end_full_month(self):
        self.assertEqual(create_hive_date_range_filter("1/5/2019", "4/30/2019"),
                        """((year = '2019' and month = '01' and day in ('05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31'))
  or (year = '2019' and month in ('02', '03', '04'))""")

    def test_span_multiple_months_same_year_start_and_end_full_month(self):
        self.assertEqual(create_hive_date_range_filter("1/1/2019", "4/30/2019"),
                        """((year = '2019' and month in ('01', '02', '03', '04'))""")

    def test_span_multiple_months_boundary_over_year_boundary(self):
        self.assertEqual(create_hive_date_range_filter("10/22/2019", "11/4/2020"),
                        """((year = '2019' and month = '10' and day in ('22', '23', '24', '25', '26', '27', '28', '29', '30', '31'))
  or (year = '2019' and month in ('11', '12')
  or (year = '2020' and month in ('01', '02', '03', '04', '05', '06', '07', '08', '09', '10')
  or (year = '2020' and month = '11' and day in ('01', '02', '03', '04')))""")

    def test_span_multiple_months_boundary_over_multiple_year_boundary(self):
        self.assertEqual(create_hive_date_range_filter("10/22/2017", "11/4/2020"),
                        """((year = '2017' and month = '10' and day in ('22', '23', '24', '25', '26', '27', '28', '29', '30', '31'))
  or (year = '2017' and month in ('11', '12')
  or (year = '2018')
  or (year = '2019')
  or (year = '2020' and month in ('01', '02', '03', '04', '05', '06', '07', '08', '09', '10')
  or (year = '2020' and month = '11' and day in ('01', '02', '03', '04')))""")

    def test_jan1_dec31_single_year(self):
        self.assertEqual(create_hive_date_range_filter("1/1/2018", "12/31/2018"),
                        """((year = '2018'))""")

    def test_jan1_dec31_multiple_year(self):
        self.assertEqual(create_hive_date_range_filter("1/1/2018", "12/31/2019"),
                        """((year = '2018')
  or (year = '2019'))""")

 
    def test_leap_year(self):
        # ugh, not sure how to test this
        # test for going to feb 19 - should only work in a leap year but...
        self.assertEqual(create_hive_date_range_filter("2/10/2019", "2/28/2019"), "this test always fails for now ")
        with self.assertRaises(ValueError):
            create_hive_date_range_filter("2/10/2019", "2/29/2019")
