import web
from memrise import memrise

import datetime
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
from utils.dateformat import date_format


class my_progress:
    def GET(self):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        USE_SUNDAY_FIRST = web.ctx.i18n.formats.get("FIRST_DAY_OF_WEEK", 0) == 0

        def day_of_week(date):
            weekday = date.weekday()

            if USE_SUNDAY_FIRST:
                return (weekday + 1) % 7
            return weekday

        # Beginning (first day, either monday or sunday, of first week to show) and end date (today)
        end_date = datetime.date.today()

        start_date = end_date - relativedelta(months=12)
        start_date -= relativedelta(days=day_of_week(start_date))

        # Get the number of things learned each day
        dt = datetime.datetime.combine(start_date, datetime.datetime.min.time())

        progress = memrise.my_progress_summary(sync_token=int(dt.timestamp()) - 1)

        # Labels of days, in the order we should display then
        # ie [{'label': 'Sunday', 'label_short': 'Sun'}...]
        date_increment = relativedelta(days=1)
        date = start_date
        days_of_week = []

        for i in range(0, 7):
            days_of_week.append(
                {
                    "label": date_format(date, "%A"),
                    "label_short": date_format(date, "%a"),
                }
            )
            date += date_increment

        # Build the listing of weeks to show, with the associated progress
        # ie [{...5: ('2026-03-06', 47), 6: ('2026-03-07', 0)}, {0: ('2026-03-08', 0)}]
        months = OrderedDict({})
        weeks = []

        counts = []
        total = 0

        date = start_date
        while date <= end_date:
            week = {}

            # Add days within that week and the progress for these days
            for i in range(0, 7):
                date_fmt = date_format(date, web.ctx.i18n.formats.get("DATE_FORMAT", "%x"))

                month = date.strftime("%Y-%m")
                day = date.strftime("%d")

                count = progress.get(month, {}).get(day, 0)
                week[i] = (date_fmt, count)

                # Keep track of our counts in a stem&leaf chart
                # ie {5: [1], 0: [6, 3, 1, 1, 4], 2: [2], 11: [6], 4: [7, 7], 9: [2]}
                if count:
                    counts.append(count)
                    total += 1

                date += date_increment
                if date > end_date:
                    break

            weeks.append(week)

            # Build month headers
            # ie {'2025-03': {'count_weeks': 4, 'label': 'March', 'label_short': 'Mar'}}
            if month not in months:
                months[month] = {
                    "count_weeks": 0,
                    "label": date_format(date, "%B"),
                    "label_short": date_format(date, "%b"),
                }
            months[month]["count_weeks"] += 1

        # Build groups (deciding at which threshold we show data-level="0"...data-level="4")
        # so that there's roughly the same amount of counts in each level
        thresholds = [1]
        counts = sorted(counts)

        n_groups = 4
        group_size = int(total / n_groups) if total else 1

        for k in range(group_size, group_size * 4, group_size):
            thresholds.append(counts[k - 1])

        # ie [(4, 47), (3, 30), (2, 4), (1, 1)]
        thresholds = [(i + 1, t) for i, t in enumerate(thresholds)]
        thresholds.reverse()

        def get_level(thresholds):
            def f(value):
                for item in thresholds:
                    level, threshold = item

                    if value >= threshold:
                        return level
                return 0

            return f

        fn = get_level(thresholds=thresholds)

        html = web.config.template.prender.progress_heatmap(months, weeks, days_of_week, fn)["__body__"]

        web.header("Content-type", "text/plain")
        return html
