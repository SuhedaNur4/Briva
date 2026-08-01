import sqlite3
import matplotlib.pyplot as plt
import os
from collections import Counter

# Connect to database
db_path = instance/briva.db
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get data for tables
cursor.execute(SELECT COUNT(*) FROM users)
total_users = cursor.fetchone()[0]

cursor.execute(SELECT COUNT(*) FROM organizations)
total_orgs = cursor.fetchone()[0]

cursor.execute(SELECT COUNT(*) FROM events)
total_events = cursor.fetchone()[0]

cursor.execute(SELECT COUNT(*) FROM event_applications)
total_applications = cursor.fetchone()[0]

print(fTotal Users: {total_users})
print(fTotal Organizations: {total_orgs})
print(fTotal Events: {total_events})
print(fTotal Applications: {total_applications})

# Graph 1: Events by Category
cursor.execute(SELECT category FROM events)
categories = [row[0] for row in cursor.fetchall()]
cat_counts = Counter(categories)

plt.figure(figsize=(8, 8))
plt.pie(cat_counts.values(), labels=cat_counts.keys(), autopct=%1.1f%%, startangle=140, colors=plt.cm.Set3.colors)
plt.title(Etkinliklerin Kategorilere Göre Dağılımı)
plt.tight_layout()
plt.savefig(ProjectManagement/Sprint3Documents/sprint3_events_by_category.png, dpi=300)
plt.close()

# Graph 2: Organizations by City
cursor.execute(SELECT city FROM organizations)
cities = [row[0] for row in cursor.fetchall()]
city_counts = Counter(cities)

# Sort by count
sorted_cities = dict(sorted(city_counts.items(), key=lambda item: item[1], reverse=True))

plt.figure(figsize=(10, 6))
plt.bar(sorted_cities.keys(), sorted_cities.values(), color=#059669)
plt.title(STK larin Sehirlere Gore Dagilimi)
plt.xlabel(Sehir)
plt.ylabel(STK Sayisi)
plt.xticks(rotation=45, ha=right)
plt.tight_layout()
plt.savefig(ProjectManagement/Sprint3Documents/sprint3_orgs_by_city.png, dpi=300)
plt.close()

print(Graphs generated.)
