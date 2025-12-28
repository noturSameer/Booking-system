import sqlite3
import threading
import time
import random


def init_database():
    conn = sqlite3.connect('booking.db', check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute('DROP TABLE IF EXISTS flights')
    cursor.execute('DROP TABLE IF EXISTS bookings')

    cursor.execute('''
        CREATE TABLE flights (
            id INTEGER PRIMARY KEY,
            flight_number TEXT UNIQUE,
            total_seats INTEGER,
            available_seats INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flight_number TEXT,
            customer_name TEXT,
            booking_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        INSERT INTO flights (flight_number, total_seats, available_seats)
        VALUES ('CA100', 10, 10)
    ''')

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")


def book_flight_unsafe(flight_number, customer_name):
    conn = sqlite3.connect('booking.db', check_same_thread=False)
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT available_seats FROM flights WHERE flight_number = ?',
                       (flight_number,))
        result = cursor.fetchone()

        if result is None:
            return False, "Flight not found"

        available_seats = result[0]

        time.sleep(random.uniform(0.01, 0.05))

        if available_seats > 0:
            new_seats = available_seats - 1
            cursor.execute('UPDATE flights SET available_seats = ? WHERE flight_number = ?',
                           (new_seats, flight_number))

            cursor.execute('INSERT INTO bookings (flight_number, customer_name) VALUES (?, ?)',
                           (flight_number, customer_name))

            conn.commit()
            return True, f"✅ Booking successful for {customer_name}! Seats left: {new_seats}"
        else:
            return False, "❌ No seats available"

    except Exception as e:
        conn.rollback()
        return False, f"Error: {str(e)}"
    finally:
        conn.close()


def book_flight_safe(flight_number, customer_name):
    conn = sqlite3.connect('booking.db', check_same_thread=False,
                           isolation_level='EXCLUSIVE')
    cursor = conn.cursor()

    try:
        cursor.execute('BEGIN EXCLUSIVE')

        cursor.execute('SELECT available_seats FROM flights WHERE flight_number = ?',
                       (flight_number,))
        result = cursor.fetchone()

        if result is None:
            conn.rollback()
            return False, "Flight not found"

        available_seats = result[0]

        time.sleep(random.uniform(0.01, 0.05))

        if available_seats > 0:
            new_seats = available_seats - 1
            cursor.execute('UPDATE flights SET available_seats = ? WHERE flight_number = ?',
                           (new_seats, flight_number))

            cursor.execute('INSERT INTO bookings (flight_number, customer_name) VALUES (?, ?)',
                           (flight_number, customer_name))

            conn.commit()
            return True, f"✅ Booking successful for {customer_name}! Seats left: {new_seats}"
        else:
            conn.rollback()
            return False, "❌ No seats available"

    except Exception as e:
        conn.rollback()
        return False, f"Error: {str(e)}"
    finally:
        conn.close()


def test_unsafe_booking(num_customers=15):
    print("\n" + "=" * 70)
    print("🔴 TESTING UNSAFE BOOKING (Race Condition)")
    print("=" * 70)

    init_database()

    threads = []
    results = []

    def booking_thread(customer_id):
        success, message = book_flight_unsafe('CA100', f'Customer_{customer_id}')
        results.append((customer_id, success, message))
        print(f"Thread {customer_id:2d}: {message}")

    print(f"\n🚀 Starting {num_customers} concurrent booking requests...\n")

    for i in range(num_customers):
        thread = threading.Thread(target=booking_thread, args=(i + 1,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    successful_bookings = sum(1 for _, success, _ in results if success)

    conn = sqlite3.connect('booking.db')
    cursor = conn.cursor()
    cursor.execute('SELECT available_seats FROM flights WHERE flight_number = ?', ('CA100',))
    remaining_seats = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM bookings WHERE flight_number = ?', ('CA100',))
    total_bookings = cursor.fetchone()[0]
    conn.close()

    print("\n" + "=" * 70)
    print("📊 RESULTS (UNSAFE BOOKING):")
    print("=" * 70)
    print(f"   Total booking attempts:    {num_customers}")
    print(f"   Successful bookings:       {successful_bookings}")
    print(f"   Total bookings in DB:      {total_bookings}")
    print(f"   Remaining seats:           {remaining_seats}")
    print(f"   Expected bookings:         10 (total seats)")
    print("=" * 70)

    if total_bookings > 10:
        print(f"   ⚠️  OVERBOOKING DETECTED: {total_bookings - 10} extra bookings!")
        print(f"   ⚠️  This is a RACE CONDITION bug!")
    else:
        print("   ✅ No overbooking (lucky this time, but bug still exists!)")

    print("=" * 70)


def test_safe_booking(num_customers=15):
    print("\n" + "=" * 70)
    print("🟢 TESTING SAFE BOOKING (With Transaction Protection)")
    print("=" * 70)

    init_database()

    threads = []
    results = []

    def booking_thread(customer_id):
        success, message = book_flight_safe('CA100', f'Customer_{customer_id}')
        results.append((customer_id, success, message))
        print(f"Thread {customer_id:2d}: {message}")

    print(f"\n🚀 Starting {num_customers} concurrent booking requests...\n")

    for i in range(num_customers):
        thread = threading.Thread(target=booking_thread, args=(i + 1,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    successful_bookings = sum(1 for _, success, _ in results if success)
    failed_bookings = num_customers - successful_bookings

    conn = sqlite3.connect('booking.db')
    cursor = conn.cursor()
    cursor.execute('SELECT available_seats FROM flights WHERE flight_number = ?', ('CA100',))
    remaining_seats = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM bookings WHERE flight_number = ?', ('CA100',))
    total_bookings = cursor.fetchone()[0]
    conn.close()

    print("\n" + "=" * 70)
    print("📊 RESULTS (SAFE BOOKING):")
    print("=" * 70)
    print(f"   Total booking attempts:    {num_customers}")
    print(f"   Successful bookings:       {successful_bookings}")
    print(f"   Failed bookings:           {failed_bookings}")
    print(f"   Total bookings in DB:      {total_bookings}")
    print(f"   Remaining seats:           {remaining_seats}")
    print(f"   Expected bookings:         10 (total seats)")
    print("=" * 70)

    if total_bookings == 10 and remaining_seats == 0:
        print("   ✅ PERFECT! No overbooking, transaction protection works!")
    else:
        print("   ⚠️  Something went wrong!")

    print("=" * 70)


def compare_both_methods():
    print("\n" + "=" * 70)
    print("🔬 COMPARATIVE ANALYSIS: UNSAFE vs SAFE")
    print("=" * 70)

    print("\n1️⃣  Running UNSAFE booking test...")
    time.sleep(1)
    test_unsafe_booking(15)

    print("\n\n⏳ Waiting 2 seconds before next test...\n")
    time.sleep(2)

    print("2️⃣  Running SAFE booking test...")
    time.sleep(1)
    test_safe_booking(15)

    print("\n" + "=" * 70)
    print("📝 CONCLUSION:")
    print("=" * 70)
    print("   Unsafe version: Shows RACE CONDITION (overbooking)")
    print("   Safe version:   Uses TRANSACTION to prevent race condition")
    print("=" * 70)


def main():
    print("\n" + "=" * 70)
    print("✈️  CENTRUM AIR BOOKING SYSTEM")
    print("    Race Condition Demonstration Project")
    print("=" * 70)
    print("\nThis project demonstrates:")
    print("  • Critical Section Problem")
    print("  • Race Condition (Overbooking)")
    print("  • Database Transaction Solution")
    print("=" * 70)

    while True:
        print("\n📋 MENU:")
        print("=" * 70)
        print("1. Test UNSAFE booking (shows race condition)")
        print("2. Test SAFE booking (with transaction protection)")
        print("3. Run BOTH tests (comparison)")
        print("4. Exit")
        print("=" * 70)

        choice = input("\n👉 Enter your choice (1-4): ").strip()

        if choice == '1':
            test_unsafe_booking(15)
            input("\n⏸  Press Enter to continue...")

        elif choice == '2':
            test_safe_booking(15)
            input("\n⏸  Press Enter to continue...")

        elif choice == '3':
            compare_both_methods()
            input("\n⏸  Press Enter to continue...")

        elif choice == '4':
            print("\n" + "=" * 70)
            print("👋 Thank you for using Centrum Air Booking System!")
            print("=" * 70)
            break

        else:
            print("\n❌ Invalid choice! Please enter 1, 2, 3, or 4.")


if __name__ == '__main__':
    main()
