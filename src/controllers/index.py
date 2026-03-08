import web
from requests.exceptions import HTTPError
from memrise import memrise

# fmt: off
urls = (
    r"/home/leaderboard", "leaderboard",
    r"/home", "index",
    r"/about", "about",
    r"/progress", "progress",
    r"/", "index",
)
# fmt: on


class index:
    def GET(self):
        if not web.ctx.session.get("loggedin", False):
            return web.config.template.render.index()
        else:
            return web.config.template.render.dashboard("courses", False, False)


class leaderboard:
    def GET(self):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        _GET = web.input(period="alltime")
        try:
            leaderboard = memrise.my_leaderboard(_GET.period)
        except HTTPError as e:
            if e.response.status_code == 403:
                return web.config.template.prender._403()
            else:
                print(e)
                return web.config.template.prender._404()

        return web.config.template.render.dashboard("leaderboard", _GET.period, leaderboard)


class progress:
    def GET(self):
        if not web.ctx.session.get("loggedin", False):
            raise web.Unauthorized()

        import datetime
        from dateutil.relativedelta import relativedelta
        from collections import OrderedDict
        from math import floor

        USE_SUNDAY_FIRST = 1
        def day_of_week(date):
            weekday = date.weekday()

            if USE_SUNDAY_FIRST:
                return (weekday + 1) % 7
            return weekday

        # Beginning and end date
        end_date = datetime.date.today()
        # end_date += relativedelta(days=6 - day_of_week(end_date)) # sunday of last week (0: monday, 6: sunday)

        start_date = end_date - relativedelta(months=12)
        start_date -= relativedelta(days=day_of_week(start_date)) # monday of first week

        # Get the number of things learned each day
        progress = memrise.my_progress_summary(
            sync_token=int(datetime.datetime.combine(start_date, datetime.datetime.min.time()).timestamp())-1
        )

        # Build the listing of weeks to show
        date_increment = relativedelta(days=1)

        date = start_date
        days_of_week = []

        for i in range(0,7):
            days_of_week.append({
                "label": date.strftime("%A"),
                "label_short": date.strftime("%a"),
            })
            date += date_increment

        date = start_date
        months = OrderedDict({})
        weeks = []

        min_value = None
        max_value = None

        while date <= end_date:
            week = {
                "days": {},
            }
            # '2026-03': {'01': 47, '02': 30, '03': 47, '04': 92, '05': 35}

            # Add days within that week and the progress for these days
            for i in range(0,7):
                date_fmt = date.strftime("%Y-%m-%d")

                month = date.strftime("%Y-%m")
                day = date.strftime("%d")

                count = progress.get(month, {}).get(day, 0)
                week["days"][i] = (date_fmt, count)

                # Keep min and max value of progress within start and end date
                if min_value is None or count < min_value:
                    min_value = count

                if max_value is None or count > max_value:
                    max_value = count

                date += date_increment
                if date > end_date:
                    break
            weeks.append(week)

            # Build month headers
            if month not in months:
                months[month] = {
                    "count_weeks": 0,
                    "label": date.strftime("%B"),  # TODO set localization?
                    "label_short": date.strftime("%b"),
                }
            months[month]["count_weeks"] += 1

        # Decide at which threshold we show data-level="0"...data-level="4"
        c = floor((max_value - min_value) / 4) if min_value != max_value else 1
        if c < 1:
            c = 1

        def get_level(thresholds):
            def f(value):
                for item in thresholds:
                    level, threshold = item

                    if value >= threshold:
                        return level
                if value >= 1:
                    return 1
                return 0
            return f

        fn = get_level(thresholds=list(reversed([
            (i, c*i) for i in range(2,5)
        ])))

        return web.config.template.render.progress_heatmap(months, weeks, days_of_week, fn)


class about:
    def GET(self):
        return web.config.template.render.about()


app = web.application(urls, locals(), autoreload=False)
