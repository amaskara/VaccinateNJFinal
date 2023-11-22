from datetime import datetime
from datetime import timedelta

# converts date string from VaccinateNJ's database
# to a string that indicates the time last updated 
# (ie. 2 minutes ago, 1 hour ago, 3 days ago, etc.)
def convertDate(dateStr):
    year = dateStr[0:4]
    month = dateStr[5:7]
    day = dateStr[8:10]
    hour = dateStr[11:13]
    minute = dateStr[14:16]
    second = dateStr[17:19]

    now = datetime.utcnow()
    now_year = str(now.year)
    now_month = str(now.month)
    now_day = str(now.day)
    now_hour = str(now.hour)
    now_minute = str(now.minute)
    now_second = str(now.second)
    if len(now_month) == 1:
        now_month = '0' + now_month
    if len(now_day) == 1:
        now_day = '0' + now_day
    if len(now_hour) == 1:
        now_hour = '0' + now_hour
    if len(now_minute) == 1:
        now_minute = '0' + now_minute

    datetimeFormat = '%Y-%m-%d %H:%M:%S.%f'
    dateNow = now_year + '-' + now_month + '-' + now_day + ' ' + \
        now_hour + ':' + now_minute + ':' + now_second + '.0'
    dateUpdated = year + '-' + month + '-' + day + ' ' + \
        hour + ':' + minute + ':' + second + '.0'
    diff = datetime.strptime(dateNow, datetimeFormat) \
         - datetime.strptime(dateUpdated, datetimeFormat)

    if (diff.days < 0 or diff.seconds < 0):
        retStr = 'Time N/A'
        return retStr
        
    if (diff.days > 30):
        if (diff.days // 30 == 1):
            retStr = '1 Month Ago'
        else:
            retStr = str(diff.days // 30) + ' Months Ago'
        return retStr
    if (diff.days == 0):
        numHours = diff.seconds // 3600
        if (numHours == 0):
            numMinutes = diff.seconds // 60
            if (numMinutes == 0):
                retStr = 'Less Than a Minute Ago'
                return retStr
            else:
                if (numMinutes == 1):
                    retStr = '1 Minute Ago'
                else:
                    retStr = str(numMinutes) + ' Minutes Ago'
                return retStr
        else:
            if (numHours == 1):
                retStr = '1 Hour Ago'
            else:
                retStr = str(numHours) + ' Hours Ago'
            return retStr
    else:
        if (diff.days == 1):
            retStr = '1 Day Ago'
        else:
            retStr = str(diff.days) + ' Days Ago'
        return retStr
