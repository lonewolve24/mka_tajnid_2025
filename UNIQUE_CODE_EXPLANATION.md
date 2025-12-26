# Unique Code System Explanation

## Overview
The unique code system generates codes like `2025-0001`, `2025-0002`, etc. for each registration.

## Two Ways Codes Are Generated

### 1. **Automatic Generation (for new registrations)**
When you create a new registration, the `save()` method automatically generates a code:

```python
def save(self, *args, **kwargs):
    if not self.unique_code:
        self.generate_unique_code()  # Auto-generate if missing
    super().save(*args, **kwargs)
```

**How it works:**
- Checks if `unique_code` already exists
- If not, calls `generate_unique_code()`
- Finds the highest number for the current year (e.g., if `2025-0042` exists, next is `2025-0043`)
- Ensures uniqueness by checking if the code already exists
- Formats as `YEAR-NNNN` (e.g., `2025-0001`)

### 2. **Bulk Backfill (for existing registrations)**
For registrations that already exist without codes, we use the **Manager's `backfill_unique_codes()` method**.

## Why Use a Manager?

### What is a Django Manager?
A **Manager** is Django's interface for database operations. Every model has a default manager called `objects`:

```python
# Default manager (what Django gives you)
Registration.objects.all()  # Get all registrations
Registration.objects.filter(region='URR')  # Filter
Registration.objects.create(...)  # Create new
```

### Why Create a Custom Manager?
We created `RegistrationManager` to add **custom methods** that work on collections of registrations, not just single instances.

**Without Manager (only instance method):**
```python
# You'd have to do this for EACH registration:
for reg in Registration.objects.filter(unique_code__isnull=True):
    reg.generate_unique_code()  # Instance method
    reg.save()
```

**With Manager (bulk operation):**
```python
# One line to backfill ALL missing codes:
Registration.objects.backfill_unique_codes()  # Manager method
```

### Benefits of Using Manager:
1. **Bulk Operations**: Process many records efficiently
2. **Reusable**: Can be called from anywhere (views, commands, admin)
3. **Organized**: Keeps bulk logic separate from instance logic
4. **Transaction Safety**: Can wrap in database transactions

## How the Manager Works

### Step-by-Step Breakdown:

```python
class RegistrationManager(models.Manager):
    def backfill_unique_codes(self):
        # Step 1: Get all registrations without codes, ordered by creation date
        registrations = self.filter(unique_code__isnull=True).order_by('created_at', 'id')
        
        # Step 2: Group by year (2024, 2025, etc.)
        by_year = defaultdict(list)
        for registration in registrations:
            year = registration.created_at.year
            by_year[year].append(registration)
        
        # Step 3: Process each year separately
        with transaction.atomic():  # All-or-nothing database operation
            for year, year_registrations in sorted(by_year.items()):
                # Step 4: Find highest existing number for this year
                existing_codes = self.filter(
                    unique_code__startswith=f"{year}-"
                ).values_list('unique_code', flat=True)
                
                max_num = 0
                for code in existing_codes:
                    num = int(code.split('-')[1])  # Extract number from "2025-0042"
                    max_num = max(max_num, num)
                
                # Step 5: Assign sequential numbers starting from max_num + 1
                for i, registration in enumerate(year_registrations, start=1):
                    next_num = max_num + i
                    registration.unique_code = f"{year}-{next_num:04d}"
                    registration.save(update_fields=['unique_code'])
```

### Example:
If you have:
- `2025-0001`, `2025-0002`, `2025-0003` (already have codes)
- 3 registrations from 2025 without codes

The manager will:
1. Find max_num = 3 (from existing codes)
2. Assign: `2025-0004`, `2025-0005`, `2025-0006` to the 3 missing ones

## Manager vs Instance Method

| Aspect | Instance Method (`generate_unique_code()`) | Manager Method (`backfill_unique_codes()`) |
|--------|-------------------------------------------|-------------------------------------------|
| **Works on** | Single registration | Multiple registrations |
| **Called as** | `registration.generate_unique_code()` | `Registration.objects.backfill_unique_codes()` |
| **Use case** | New registrations (automatic) | Bulk backfill existing data |
| **Transaction** | Single save | Wrapped in transaction (all-or-nothing) |
| **Efficiency** | One at a time | Processes all at once |

## How to Use

### For New Registrations (Automatic):
```python
# Just create normally - code is auto-generated
registration = Registration.objects.create(
    first_name="John",
    last_name="Doe",
    region="URR",
    auxiliary_body="Khuddam"
)
# unique_code is automatically set to something like "2025-0001"
```

### For Existing Registrations (Bulk Backfill):
```python
# In Django shell or management command:
from tagnid.models import Registration

# Backfill all missing codes
count = Registration.objects.backfill_unique_codes()
print(f"Updated {count} registrations")
```

### Via Management Command:
```bash
python manage.py backfill_unique_codes
```

## Summary

- **Manager** = Tool for bulk operations on collections
- **Instance Method** = Tool for single object operations
- **Why both?** 
  - Instance method handles new registrations automatically
  - Manager method handles bulk backfill of existing data efficiently
  - They work together to ensure all registrations have unique codes

