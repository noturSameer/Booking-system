# 🛫 Centrum Air Booking System - Race Condition Demo

## 📋 Project Description

This project demonstrates the **critical section problem** in a booking system, specifically showing how **race conditions** can lead to overbooking (like the famous Centrum Air case) and how to prevent it using **database transactions**.

## 🎯 Project Objectives

1. Demonstrate race condition in a real-world scenario (flight booking)
2. Show how overbooking happens without proper synchronization
3. Implement solution using database transactions
4. Compare unsafe vs safe implementations

## 📁 Project Structure

```
booking-system/
│
├── booking_system.py      # Main backend code (Python)
├── index.html             # Web interface (optional visualization)
├── README.md              # This file
├── report.pdf             # Detailed explanation document
└── booking.db             # SQLite database (auto-generated)
```

## 🔧 Requirements

- Python 3.7 or higher
- No external libraries needed (uses built-in modules)

## 🚀 How to Run

### Method 1: Console Testing (No HTML)

```bash
# Run the main program
python booking_system.py

# Choose option:
# 1 - Test unsafe booking (shows race condition)
# 2 - Test safe booking (with protection)
# 3 - Start web server
# 4 - Exit
```

### Method 2: Web Interface

```bash
# Start the program
python booking_system.py

# Choose option 3 to start web server
# Open browser: http://localhost:8000
```

## 🎮 How to Use

### Console Mode:

1. Run `python booking_system.py`
2. Select option **1** to see unsafe booking (race condition)
   - 15 threads will try to book simultaneously
   - You'll see OVERBOOKING happen!
3. Select option **2** to see safe booking (with transaction)
   - 15 threads will try to book simultaneously
   - Only 10 bookings succeed (no overbooking)

### Web Interface Mode:

1. Click "Book (Unsafe)" to book one ticket without protection
2. Click "Book 15 Times (Show Race Condition)" to simulate race condition
3. Watch the status panel - you'll see more than 10 bookings!
4. Click "Reset System" to start fresh
5. Try "Book (Safe)" and "Book 15 Times (Protected)"
6. Notice that only 10 bookings succeed (correct behavior)

## 🔴 Problem: Race Condition (Unsafe Booking)

### How Overbooking Happens:

```
Time    Thread 1              Thread 2              Thread 3
----    -----------------     -----------------     -----------------
t1      Read: 10 seats        
t2                            Read: 10 seats
t3                                                  Read: 10 seats
t4      Check: 10 > 0 ✓
t5                            Check: 10 > 0 ✓
t6                                                  Check: 10 > 0 ✓
t7      Write: 9 seats
t8                            Write: 9 seats        
t9                                                  Write: 9 seats
t10     Insert booking
t11                           Insert booking
t12                                                 Insert booking

Result: All 3 bookings succeed even though only 1 seat should be sold!
```

### Code Implementation (Unsafe):

```python
def book_flight_unsafe(flight_number, customer_name):
    # Step 1: Read available seats
    cursor.execute('SELECT available_seats FROM flights WHERE flight_number = ?', 
                  (flight_number,))
    available_seats = result[0]
    
    # PROBLEM: Other threads can read the same value here!
    time.sleep(random.uniform(0.01, 0.05))  # Simulates processing delay
    
    # Step 2: Check and book
    if available_seats > 0:
        new_seats = available_seats - 1
        cursor.execute('UPDATE flights SET available_seats = ?', (new_seats,))
        cursor.execute('INSERT INTO bookings VALUES (?)', (customer_name,))
```

## 🟢 Solution: Database Transaction (Safe Booking)

### How Transaction Prevents Overbooking:

```
Time    Thread 1              Thread 2              Thread 3
----    -----------------     -----------------     -----------------
t1      Lock DB & Read: 10
t2                            WAIT (DB locked)
t3                                                  WAIT (DB locked)
t4      Check: 10 > 0 ✓
t5      Write: 9 seats
t6      Insert booking
t7      Unlock DB
t8                            Lock DB & Read: 9
t9                                                  WAIT (DB locked)
t10                           Check: 9 > 0 ✓
t11                           Write: 8 seats
t12                           Insert booking
t13                           Unlock DB
t14                                                 Lock DB & Read: 8

Result: Bookings happen one at a time (serialized). No race condition!
```

### Code Implementation (Safe):

```python
def book_flight_safe(flight_number, customer_name):
    conn = sqlite3.connect('booking.db', isolation_level='EXCLUSIVE')
    
    try:
        # Begin exclusive transaction - LOCKS the database
        cursor.execute('BEGIN EXCLUSIVE')
        
        # Step 1: Read available seats (now protected)
        cursor.execute('SELECT available_seats FROM flights WHERE flight_number = ?')
        available_seats = result[0]
        
        # No other thread can access the database here!
        time.sleep(random.uniform(0.01, 0.05))
        
        # Step 2: Check and book (atomic operation)
        if available_seats > 0:
            new_seats = available_seats - 1
            cursor.execute('UPDATE flights SET available_seats = ?', (new_seats,))
            cursor.execute('INSERT INTO bookings VALUES (?)', (customer_name,))
        
        conn.commit()  # Release lock
    except:
        conn.rollback()  # Release lock on error
```

## 📊 Key Concepts Demonstrated

### 1. Critical Section
The code section where shared resource (available_seats) is accessed:
```python
# CRITICAL SECTION START
available_seats = read_from_database()
if available_seats > 0:
    available_seats -= 1
    write_to_database(available_seats)
# CRITICAL SECTION END
```

### 2. Race Condition
When two or more threads access shared data simultaneously without synchronization.

### 3. Read/Write Conflict
- **Read**: Multiple threads read same value (10 seats)
- **Write**: All threads write based on outdated value
- **Result**: Data corruption (overbooking)

### 4. Solution: Database Transaction with EXCLUSIVE lock
- Only one transaction can execute at a time
- Other transactions must wait
- Guarantees atomic operations (all-or-nothing)

## 🧪 Expected Results

### Unsafe Booking (Race Condition):
```
Total booking attempts: 15
Successful bookings: 12-15 (varies)
Total bookings in DB: 12-15
Remaining seats: -2 to -5 (NEGATIVE!)
⚠️ OVERBOOKING: 2-5 extra bookings!
```

### Safe Booking (Protected):
```
Total booking attempts: 15
Successful bookings: 10
Total bookings in DB: 10
Remaining seats: 0
✅ CORRECT! No overbooking.
```

## 🎓 Learning Outcomes

After completing this project, you should understand:

1. ✅ What is a race condition
2. ✅ How race conditions cause real-world problems (overbooking)
3. ✅ What is a critical section
4. ✅ How to identify read/write conflicts
5. ✅ How database transactions prevent race conditions
6. ✅ The importance of synchronization in concurrent systems

## 📚 Real-World Context: Centrum Air Case

Centrum Air became infamous for overbooking flights due to poor synchronization in their booking system. When multiple agents booked tickets simultaneously, the system would:

1. Read available seats (e.g., 10 seats)
2. Multiple agents see "10 seats available"
3. All agents book simultaneously
4. Result: 15 bookings for 10 seats!

This led to:
- Angry customers
- Compensations ($$$)
- Legal issues
- Reputation damage

**This project recreates that exact problem and shows how to fix it!**

## 🔍 Testing Checklist

- [ ] Run unsafe booking - see overbooking
- [ ] Run safe booking - no overbooking
- [ ] Test web interface - try both modes
- [ ] Check database state after tests
- [ ] Verify that safe mode never exceeds 10 bookings
- [ ] Understand why race condition happens
- [ ] Understand how transaction prevents it

## 📧 Submission

Create a GitHub repository with:
- `booking_system.py` (main backend code)
- `index.html` (web interface)
- `README.md` (this file)
- `report.pdf` (detailed explanation)

Share the GitHub link via email.

## 🎯 Grading Criteria

1. **Backend Code** (50%)
   - Working race condition demo
   - Working transaction protection
   - Clean, commented code

2. **Explanation** (40%)
   - Understanding of critical section
   - Clear explanation of race condition
   - Correct solution implementation

3. **Demonstration** (10%)
   - Ability to run and explain code
   - Understanding of results
   - Defense during office visit

## 👨‍💻 Author

Samandar Mirxosilov
230146
