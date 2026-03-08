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

        # Beginning (first day, either monday or sunday, of first week to show) and end date (today)
        end_date = datetime.date.today()

        start_date = end_date - relativedelta(months=12)
        start_date -= relativedelta(days=day_of_week(start_date))

        # Get the number of things learned each day
        progress = memrise.my_progress_summary(
            sync_token=int(datetime.datetime.combine(start_date, datetime.datetime.min.time()).timestamp())-1
        )

        # Labels of days, in the order we should display then
        # ie [{'label': 'Sunday', 'label_short': 'Sun'}...]
        date_increment = relativedelta(days=1)
        date = start_date
        days_of_week = []

        for i in range(0,7):
            days_of_week.append({
                "label": date.strftime("%A"),
                "label_short": date.strftime("%a"),
            })
            date += date_increment

        # Build the listing of weeks to show, with the associated progress
        # ie [{...5: ('2026-03-06', 47), 6: ('2026-03-07', 0)}, {0: ('2026-03-08', 0)}]
        date = start_date
        months = OrderedDict({})
        weeks = []

        stem_and_leaf = {}
        bin_size = 10
        total = 0

        while date <= end_date:
            week = {}

            # Add days within that week and the progress for these days
            for i in range(0,7):
                date_fmt = date.strftime("%Y-%m-%d")

                month = date.strftime("%Y-%m")
                day = date.strftime("%d")

                count = progress.get(month, {}).get(day, 0)
                week[i] = (date_fmt, count)

                # Keep track of our counts in a stem&leaf chart
                # ie {5: [1], 0: [6, 3, 1, 1, 4], 2: [2], 11: [6], 4: [7, 7], 9: [2]}
                if count:
                    stem = int(count / bin_size)
                    leaf = count % bin_size

                    if stem not in stem_and_leaf:
                        stem_and_leaf[stem] = []
                    stem_and_leaf[stem].append(leaf)
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
                    "label": date.strftime("%B"),  # TODO set localization?
                    "label_short": date.strftime("%b"),
                }
            months[month]["count_weeks"] += 1

        # Build groups (deciding at which threshold we show data-level="0"...data-level="4")
        # so that there's roughly the same amount of counts in each level
        thresholds = [1]
        if total:
            stem_and_leaf = {
                stem: sorted(stem_and_leaf[stem])
                for stem in sorted(stem_and_leaf.keys())
            }

            n_groups = 4
            group_size = int(total / n_groups) if total else 1
            c = 0

            stems = list(stem_and_leaf.keys())
            while len(stems):
                stem = stems.pop(0)
                n_leaves = len(stem_and_leaf[stem])

                if c + n_leaves < group_size:
                    c += n_leaves
                    continue

                leaves = stem_and_leaf[stem]
                k = group_size - c
                thresholds.append(int(f"{stem}{leaves[k-1]}"))

                if len(thresholds) == n_groups:
                    break

                stem_and_leaf[stem] = leaves[k:]
                stems.insert(0, stem)
                c = 0

            # ie [(4, 47), (3, 30), (2, 4), (1, 1)]
            thresholds = [(i+1, t) for i, t in enumerate(thresholds)]
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

        return web.config.template.render.progress_heatmap(months, weeks, days_of_week, fn)


class about:
    def GET(self):
        return web.config.template.render.about()


app = web.application(urls, locals(), autoreload=False)
