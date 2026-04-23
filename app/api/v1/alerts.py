import resend
import smtplib
from collections import defaultdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import yfinance as yf
from datetime import datetime
from app.db.supabase import supabase
from app.core.config import settings
from app.services.logger import sys_logger

SENDER_EMAIL    = settings.SENDER_EMAIL
SENDER_PASSWORD = settings.SENDER_APP_PASSWORD

def send_squad_digest(recipient_emails: list, subject: str, html_content: str):
    """
    Sends the HTML via GMAIL smtp
    :param recipient_emails: List of email ids to which the digest will be sent
    :param subject: The subject of the email being sent
    :param html_content: The content of the email being sent
    """
    try:
        resend.api_key     = settings.RESEND_API_KEY
        r = resend.Emails.send({
            "from"   : f"StoxCircle <{settings.SENDER_EMAIL}>",
            "to"     : [settings.APP_EMAIL],
            "bcc"    : recipient_emails,
            "html"   : html_content,
            "subject": subject
        })

        sys_logger.info(f"[{datetime.now()}] Successfully sent digest {r['id']} to {len(recipient_emails)} members.")
    except Exception as e:
        sys_logger.error(f"Failed to send email: {e}")


def build_health_report_html(report_data: dict, group_name: str, time_of_day: str):
    """Generates the HTML email dynamically branded for the specific group."""

    global_pnl_str = f"+{report_data['global_pnl_pct']:.2f}%" if report_data[
                                                                     'global_pnl_pct'] >= 0 else f"{report_data['global_pnl_pct']:.2f}%"
    global_pnl_amt = f"+₹{report_data['global_pnl_amount']:,.2f}" if report_data[
                                                                         'global_pnl_amount'] >= 0 else f"-₹{abs(report_data['global_pnl_amount']):,.2f}"
    global_color = "#4ade80" if report_data['global_pnl_amount'] >= 0 else "#ef4444"

    rows_html = ""
    for pos in report_data['positions']:
        pnl_pct_str = f"+{pos['pnl_pct']:.2f}%" if pos['pnl_pct'] >= 0 else f"{pos['pnl_pct']:.2f}%"
        pnl_amt_str = f"+₹{pos['pnl_amount']:,.2f}" if pos['pnl_amount'] >= 0 else f"-₹{abs(pos['pnl_amount']):,.2f}"

        pill_bg = pos['status_color'].replace(')', ', 0.1)').replace('rgb', 'rgba') if 'rgb' in pos[
            'status_color'] else f"{pos['status_color']}20"
        if pos['status_color'] == "#4ade80": pill_bg = "rgba(74, 222, 128, 0.1)"
        if pos['status_color'] == "#60a5fa": pill_bg = "rgba(96, 165, 250, 0.1)"
        if pos['status_color'] == "#ef4444": pill_bg = "rgba(239, 68, 68, 0.1)"
        if pos['status_color'] == "#f59e0b": pill_bg = "rgba(245, 158, 11, 0.1)"
        if pos['status_color'] == "#a855f7": pill_bg = "rgba(168, 85, 247, 0.1)"

        rows_html += f"""
        <tr>
            <td style="padding: 16px; border-bottom: 1px solid #262626; width: 50%;">
                <strong style="color: #ffffff; font-size: 15px; display: block; margin-bottom: 4px;">{pos['ticker']}</strong>
                <span style="color: {pos['status_color']}; font-size: 11px; font-weight: bold; padding: 2px 6px; background-color: {pill_bg}; border-radius: 4px;">{pos['status']}</span>
            </td>
            <td align="right" style="padding: 16px; border-bottom: 1px solid #262626; width: 50%;">
                <span style="color: {pos['status_color']}; font-weight: bold; font-size: 15px; display: block; margin-bottom: 4px;">{pnl_pct_str}</span>
                <span style="color: #6b7280; font-size: 12px;">{pnl_amt_str}</span>
            </td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <body style="margin: 0; padding: 0; background-color: #0a0a0a; font-family: -apple-system, sans-serif; color: #e5e7eb; -webkit-font-smoothing: antialiased;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0a0a0a; padding: 40px 20px;">
            <tr>
                <td align="center">
                    <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 500px; background-color: #171717; border: 1px solid #262626; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
                        <tr>
                            <td style="background: linear-gradient(90deg, #3b82f6, #a855f7); padding: 24px; text-align: center;">
                                <span style="font-size: 20px; color: #ffffff; font-weight: 800; letter-spacing: 1.5px; display: block; margin-bottom: 4px;">{group_name.upper()}</span>
                                <span style="font-size: 11px; color: rgba(255,255,255,0.8); letter-spacing: 3px; text-transform: uppercase; font-weight: 600;">{time_of_day} System Report</span>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 32px 24px 16px 24px; text-align: center; border-bottom: 1px solid #262626;">
                                <span style="display: block; font-size: 12px; color: #9ca3af; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">Running Portfolio Net</span>
                                <span style="display: block; font-size: 42px; font-weight: 700; color: {global_color}; margin-bottom: 4px;">{global_pnl_str}</span>
                                <span style="display: block; font-size: 16px; color: {global_color}; font-weight: 600;">{global_pnl_amt}</span>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 24px;">
                                <span style="display: block; font-size: 13px; font-weight: 600; color: #e5e7eb; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.5px;">Active Deployments</span>
                                <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0a0a0a; border-radius: 8px; border: 1px solid #262626; overflow: hidden;">
                                    {rows_html}
                                </table>
                            </td>
                        </tr>
                        <tr>
                            <td style="background-color: #111111; padding: 20px; text-align: center; border-top: 1px solid #262626;">
                                <p style="margin: 0; font-size: 10px; color: #4b5563; text-transform: uppercase; letter-spacing: 1px;">Powered by EquityCircle</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

def run_global_market_scan(time_of_day="Mid-Day"):
    """Scans all groups, aggregates data, and sends targeted emails."""
    sys_logger.info(f"[{datetime.now()}] Starting Global {time_of_day} Scan...")

    # 1. FETCH OPEN TRADES & JOIN GROUP ID VIA COHORTS TABLE
    trades_res = supabase.table("trades").select("*, cohorts(group_id)").eq("status", "OPEN").execute()

    all_open_trades = trades_res.data

    if not all_open_trades:
        sys_logger.info("No open trades globally. Sleeping.")
        return

    # 2. EXTRACT ACTIVE GROUP IDS & FETCH MEMBER EMAILS
    active_group_ids = list(set([
        trade["cohorts"]["group_id"]
        for trade in all_open_trades
        if trade.get("cohorts")
    ]))

    groups_res = supabase.table("groups") \
        .select("id, name, group_members(user_id)") \
        .in_("id", active_group_ids) \
        .execute()

    groups_data = {}

    for group in groups_res.data:
        member_emails = []

        for member in group.get("group_members", []):
            uid = member.get("user_id")
            if uid:
                try:
                    # Use the Admin API to cross the security boundary
                    # and grab the user's email directly from auth.users
                    user_data = supabase.auth.admin.get_user_by_id(uid)
                    if user_data and user_data.user and user_data.user.email:
                        member_emails.append(user_data.user.email)
                except Exception as e:
                    sys_logger.warning(f"Could not fetch email for user {uid}: {e}")

        # Only add the group to our alert list if we found valid emails
        if member_emails:
            groups_data[group["id"]] = {
                "name": group["name"],
                "emails": member_emails
            }

    # 3. MASS YAHOO FINANCE FETCH
    tickers = list(set([t["ticker_symbol"] for t in all_open_trades]))
    try:
        live_data = yf.download(tickers, period="1d", progress=False)['Close']
        if len(tickers) == 1:
            live_prices = {tickers[0]: float(live_data.iloc[-1])}
        else:
            live_prices = {ticker: float(live_data[ticker].iloc[-1]) for ticker in tickers}
    except Exception as e:
        sys_logger.error(f"Error fetching Yahoo Finance data: {e}")
        return

    # 4. GROUP TRADES BY SQUAD
    trades_by_group = defaultdict(list)
    for trade in all_open_trades:
        grp_id = trade["cohorts"]["group_id"]
        trades_by_group[grp_id].append(trade)

    # 5. CALCULATE MATH & DISPATCH EMAILS PER SQUAD
    for group_id, trades in trades_by_group.items():
        group_info = groups_data.get(group_id)
        if not group_info or not group_info["emails"]:
            continue

        total_invested = 0
        total_current_value = 0
        positions_data = []

        for trade in trades:
            ticker = trade["ticker_symbol"]
            current_price = live_prices.get(ticker, trade["buy_price"])
            avg_price = float(trade["buy_price"])
            qty = float(trade["quantity"])

            invested = avg_price * qty
            current_value = current_price * qty
            pnl_amount = current_value - invested
            pnl_pct = ((current_price - avg_price) / avg_price) * 100

            total_invested += invested
            total_current_value += current_value

            sl_price = avg_price * 0.92
            t1_price = avg_price * 1.08
            t3_price = avg_price * 1.12

            if current_price <= sl_price * 1.01:
                status, status_color = "🔴 Near Stop Loss", "#ef4444"
            elif current_price >= t3_price:
                status, status_color = "🏆 T3 Reached", "#a855f7"
            elif current_price >= t1_price:
                status, status_color = "🟢 In Profit Zone", "#4ade80"
            elif pnl_pct > 0:
                status, status_color = "↗️ Trending Up", "#60a5fa"
            else:
                status, status_color = "↘️ Trending Down", "#f59e0b"

            positions_data.append({
                "ticker": ticker, "pnl_pct": pnl_pct, "pnl_amount": pnl_amount,
                "status": status, "status_color": status_color
            })

        global_pnl_amount = total_current_value - total_invested
        global_pnl_pct = (global_pnl_amount / total_invested * 100) if total_invested > 0 else 0

        report_data = {
            "global_pnl_pct": global_pnl_pct,
            "global_pnl_amount": global_pnl_amount,
            "positions": sorted(positions_data, key=lambda x: x['pnl_pct'], reverse=True)
        }

        html_body = build_health_report_html(report_data, group_info["name"], time_of_day)

        send_squad_digest(
            recipient_emails=group_info["emails"],
            subject=f"📊 {group_info['name']} {time_of_day} Report",
            html_content=html_body
        )