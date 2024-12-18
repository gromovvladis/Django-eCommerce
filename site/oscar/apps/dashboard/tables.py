from django_tables2 import Table

class DashboardTable(Table):
    caption = ("%d Ряд", "%d Ряды")

    def get_caption_display(self):
        # Allow overriding the caption with an arbitrary string that we cannot
        # interpolate the number of rows in
        try:
            return self.caption % self.paginator.count
        except TypeError:
            pass
        return self.caption

    class Meta:
        template_name = "oscar/dashboard/table.html"
        attrs = {"class": "table table-striped table-bordered"}
