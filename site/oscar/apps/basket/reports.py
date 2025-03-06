from oscar.core.loading import get_class, get_model

ReportGenerator = get_class("dashboard.reports.reports", "ReportGenerator")
ReportCSVFormatter = get_class("dashboard.reports.reports", "ReportCSVFormatter")
ReportHTMLFormatter = get_class("dashboard.reports.reports", "ReportHTMLFormatter")

Basket = get_model("basket", "Basket")


class OpenBasketReportCSVFormatter(ReportCSVFormatter):
    filename_template = "open-baskets-%s-%s.csv"

    def generate_csv(self, response, baskets):
        writer = self.get_csv_writer(response)
        header_row = [
            "ID Пользователя",
            "Имя",
            "Email",
            "Статус корзины",
            "Количество позиций",
            "Количество товаров",
            "Дата создания",
            "Время с момента создания",
        ]
        writer.writerow(header_row)

        for basket in baskets:
            if basket.owner:
                row = [
                    basket.owner_id,
                    basket.owner.get_full_name(),
                    basket.owner.email,
                    basket.status,
                    basket.num_lines,
                    basket.num_items,
                    self.format_datetime(basket.date_created),
                    basket.time_since_creation,
                ]
            else:
                row = [
                    basket.owner_id,
                    None,
                    None,
                    basket.status,
                    basket.num_lines,
                    basket.num_items,
                    self.format_datetime(basket.date_created),
                    self.format_timedelta(basket.time_since_creation),
                ]
            writer.writerow(row)

    def filename(self, **kwargs):
        return self.filename_template % (kwargs["start_date"], kwargs["end_date"])


class OpenBasketReportHTMLFormatter(ReportHTMLFormatter):
    filename_template = "oscar/dashboard/reports/partials/open_basket_report.html"


class OpenBasketReportGenerator(ReportGenerator):
    """
    Report of baskets which haven't been submitted yet
    """

    code = "open_baskets"
    description = "Открытые корзины"
    date_range_field_name = "date_created"
    queryset = Basket._default_manager.filter(status=Basket.OPEN)

    formatters = {
        "CSV_formatter": OpenBasketReportCSVFormatter,
        "HTML_formatter": OpenBasketReportHTMLFormatter,
    }

    def generate(self, *args, **kwargs):
        additional_data = {"start_date": self.start_date, "end_date": self.end_date}
        return self.formatter.generate_response(self.queryset, **additional_data)


class SubmittedBasketReportCSVFormatter(ReportCSVFormatter):
    filename_template = "submitted_baskets-%s-%s.csv"

    def generate_csv(self, response, baskets):
        writer = self.get_csv_writer(response)
        header_row = [
            "ID Пользователя",
            "Пользователь",
            "Статус корзины",
            "Количество позиций",
            "Количество товаров",
            "Дата создания",
            "Время между созданием и отправкой",
        ]
        writer.writerow(header_row)

        for basket in baskets:
            row = [
                basket.owner_id,
                basket.owner,
                basket.status,
                basket.num_lines,
                basket.num_items,
                self.format_datetime(basket.date_created),
                basket.time_before_submit,
            ]
            writer.writerow(row)

    def filename(self, **kwargs):
        return self.filename_template % (kwargs["start_date"], kwargs["end_date"])


class SubmittedBasketReportHTMLFormatter(ReportHTMLFormatter):
    filename_template = "oscar/dashboard/reports/partials/submitted_basket_report.html"


class SubmittedBasketReportGenerator(ReportGenerator):
    """
    Report of baskets that have been submitted
    """

    code = "submitted_baskets"
    description = "Отправленные корзины"
    date_range_field_name = "date_submitted"
    queryset = Basket._default_manager.filter(status=Basket.SUBMITTED)

    formatters = {
        "CSV_formatter": SubmittedBasketReportCSVFormatter,
        "HTML_formatter": SubmittedBasketReportHTMLFormatter,
    }

    def generate(self, *args, **kwargs):
        additional_data = {"start_date": self.start_date, "end_date": self.end_date}
        return self.formatter.generate_response(self.queryset, **additional_data)
