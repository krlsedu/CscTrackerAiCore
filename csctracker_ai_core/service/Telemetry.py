from datetime import datetime, timedelta, timezone
import logging
from csctracker_ai_core.service.ClickHouseDb import ClickHouseDb


class DateUtils:
    @staticmethod
    def get_period_dates(period: str):
        now = datetime.now(timezone.utc)
        end_date = now
        start_date = now

        if period == "1m":
            start_date = now - timedelta(minutes=1)
        elif period == "5m":
            start_date = now - timedelta(minutes=5)
        elif period == "10m":
            start_date = now - timedelta(minutes=10)
        elif period == "15m":
            start_date = now - timedelta(minutes=15)
        elif period == "30m":
            start_date = now - timedelta(minutes=30)
        elif period == "1h":
            start_date = now - timedelta(hours=1)
        elif period == "2h":
            start_date = now - timedelta(hours=2)
        elif period == "3h":
            start_date = now - timedelta(hours=3)
        elif period == "6h":
            start_date = now - timedelta(hours=6)
        elif period == "12h":
            start_date = now - timedelta(hours=12)
        elif period == "24h":
            start_date = now - timedelta(hours=24)
        elif period == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "yesterday":
            start_date = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1) - timedelta(microseconds=1)
        elif period == "week":
            start_date = now - timedelta(days=7)
        elif period == "thisWeek":
            # Início na segunda-feira
            start_date = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "month":
            start_date = now - timedelta(days=30)
        elif period == "thisMonth":
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == "year":
            start_date = now - timedelta(days=365)
        elif period == "thisYear":
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == "max":
            start_date = datetime(1970, 1, 1, tzinfo=timezone.utc)
            end_date = datetime(2099, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        else:
            start_date = now - timedelta(days=1)

        return start_date, end_date


class Telemetry:
    def __init__(self, db: ClickHouseDb = None):
        self.db = db or ClickHouseDb()

    def get_telemetry_data(self, group: str, period: str):
        start_date, end_date = DateUtils.get_period_dates(period)

        group_formats = {
            "year": "%%Y",
            "month": "%%Y-%%m",
            "day": "%%Y-%%m-%%d",
            "hour": "%%H"
        }

        group_format = group_formats.get(group, "group")
        if group_format == "group":
            group_format = "'group'"
        else:
            group_format = f"formatDateTime(e.timestamp, '{group_format}')"

        sql = f"""
SELECT e.task as task,
       {group_format}                      AS data,
       max(e.timestamp)                           AS ultimo_evento,
       count()                                    AS total_events,

       round(sum(
                     (if(e.tokens_input + e.tokens_output <= 200000,
                         (e.tokens_input / 1000000) * p.input_price_less_200 +
                         (e.tokens_output / 1000000) * p.output_price_less_200,
                         (e.tokens_input / 1000000) * p.input_price_more_200 +
                         (e.tokens_output / 1000000) * p.output_price_more_200))
                         * r.rate
             ), 4)                                AS custo_total_reais,

       round(custo_total_reais / total_events, 4) AS custo_medio_por_evento,

       round(custo_total_reais / dias_ativos, 4)  AS custo_medio_por_dia,
       round(custo_total_reais / horas_ativas, 4) AS custo_medio_por_hora,

       sum(e.tokens_input)                        AS total_input_tokens,
       sum(e.tokens_output)                       AS total_output_tokens,
       avg(e.tokens_input)                        AS avg_input_tokens,
       avg(e.tokens_output)                       AS avg_output_tokens,

       uniqExact(toDate(e.timestamp))             AS dias_ativos,
       uniqExact(toStartOfHour(e.timestamp))      AS horas_ativas,

       round(sum(
                     if(e.tokens_input + e.tokens_output <= 200000,
                        (e.tokens_input / 1000000) * p.input_price_less_200 +
                        (e.tokens_output / 1000000) * p.output_price_less_200,
                        (e.tokens_input / 1000000) * p.input_price_more_200 +
                        (e.tokens_output / 1000000) * p.output_price_more_200)
             ), 4)                                AS custo_total_usd,
       round(avgIf(time_spent, time_spent != 0),3)         as tempo_medio_por_evento,
       round(maxIf(time_spent, time_spent > 0),3)         as tempo_maximo_por_evento,
       round(minIf(time_spent, time_spent > 0),3)         as tempo_minimo_por_evento

FROM (
         SELECT *, 1 as join_key FROM ai_events
         WHERE timestamp >= %(start_date)s AND timestamp <= %(end_date)s
         ) AS e

         LEFT JOIN (
    SELECT *, replaceRegexpOne(model, '-(free|paid)$', '') as join_model
    FROM model_prices
    ORDER BY timestamp DESC
    LIMIT 1 BY model
    ) AS p ON replaceRegexpOne(e.model, '-(free|paid)$', '') = p.join_model
    ASOF
         LEFT JOIN (
    SELECT *, 1 as join_key FROM daily_exchange_rates
    ) AS r
                   ON e.join_key = r.join_key
                       AND toDate(e.timestamp) >= r.date

WHERE e.model LIKE '%%-paid'
GROUP BY data
       , e.task
ORDER BY data DESC,
         custo_medio_por_dia desc,
         custo_total_reais DESC
        """

        params = {
            "start_date": start_date,
            "end_date": end_date
        }

        try:
            client = self.db.get_ch_client()
            result = client.query(sql, parameters=params)
            data = result.named_results()
            client.close()
            return list(data)
        except Exception as e:
            logging.error(f"Erro ao obter telemetria: {e}")
            return []
