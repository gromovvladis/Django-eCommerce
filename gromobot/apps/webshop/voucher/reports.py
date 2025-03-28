from core.loading import get_class, get_model

ReportGenerator = get_class("dashboard.reports.reports", "ReportGenerator")
ReportCSVFormatter = get_class("dashboard.reports.reports", "ReportCSVFormatter")
ReportHTMLFormatter = get_class("dashboard.reports.reports", "ReportHTMLFormatter")

Voucher = get_model("voucher", "Voucher")


class VoucherReportCSVFormatter(ReportCSVFormatter):
    filename_template = "voucher-performance.csv"

    def generate_csv(self, response, vouchers):
        writer = self.get_csv_writer(response)
        header_row = [
            "Промокод",
            "Добавлено в корзину",
            "Используется в заказе",
            "Общая скидка",
        ]
        writer.writerow(header_row)

        for voucher in vouchers:
            row = [
                voucher.code,
                voucher.num_basket_additions,
                voucher.num_orders,
                voucher.total_discount,
            ]
            writer.writerow(row)


class VoucherReportHTMLFormatter(ReportHTMLFormatter):
    filename_template = "dashboard/reports/partials/voucher_report.html"


class VoucherReportGenerator(ReportGenerator):
    code = "vouchers"
    description = "Примененные промокоды"
    model_class = Voucher

    formatters = {
        "CSV_formatter": VoucherReportCSVFormatter,
        "HTML_formatter": VoucherReportHTMLFormatter,
    }
