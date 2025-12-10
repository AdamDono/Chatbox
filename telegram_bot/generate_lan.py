from datetime import date, timedelta

start_date = date(2025, 2, 1)
end_date = date(2025, 11, 30)
balance = 100.0
daily_growth = 0.10

current_date = start_date
print("# 📅 Long Term Compounding Plan (Feb - Nov)\n")
print("**Start Date**: Feb 1, 2025")
print("**Start Balance**: $100.00")
print("**Daily Growth**: 10%\n")

print("> [!CAUTION]")
print("> **The Math of 10% Daily**: You will see the numbers become **impossible** after a few months.")
print("> - By Month 3, you need to trade millions.")
print("> - By Month 5, you exceed the world's GDP.")
print("> **Realistically**: You should cap your daily target (e.g., stop compounding at $5,000 balance and just withdraw).")
print("> This plan shows the *theoretical* math if you never stopped compounding.\n")

print("| Date | Day # | Start Balance | Target (+10%) | End Balance | Lot Size (Est) |")
print("| :--- | :--- | :--- | :--- | :--- | :--- |")

day_count = 1
while current_date <= end_date:
    target = balance * daily_growth
    end_balance = balance + target
    
    # Lot size estimation (Balance / 500)
    lot_size = balance / 500
    if lot_size < 0.2: lot_size = 0.2
    
    # Format large numbers
    bal_str = f"${balance:,.2f}"
    tgt_str = f"${target:,.2f}"
    end_str = f"${end_balance:,.2f}"
    
    # Cap lot size to something realistic for Deriv (e.g. 50 max) or just show raw
    lot_str = f"{lot_size:.2f}"
    
    print(f"| {current_date.strftime('%Y-%m-%d')} | {day_count} | {bal_str} | +{tgt_str} | **{end_str}** | {lot_str} |")
    
    balance = end_balance
    current_date += timedelta(days=1)
    day_count += 1
