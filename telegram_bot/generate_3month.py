from datetime import date, timedelta

start_date = date(2025, 2, 1)
end_date = date(2025, 4, 30)
balance = 100.0
daily_growth = 0.10

current_date = start_date

print("3-Month Trading Plan (Feb - Apr 2025)\n")
print(f"{'Date':<12} | {'Day':<3} | {'Start Bal':<10} | {'Target':<9} | {'End Bal':<10}")
print("-" * 55)

day_count = 1
while current_date <= end_date:
    target = balance * daily_growth
    end_balance = balance + target
    
    print(f"{current_date.strftime('%Y-%m-%d'):<12} | {day_count:<3} | ${balance:,.2f}   | +${target:,.2f}  | ${end_balance:,.2f}")
    
    balance = end_balance
    current_date += timedelta(days=1)
    day_count += 1
