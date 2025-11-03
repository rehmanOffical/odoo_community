# How to Migrate New Fields to Database in Odoo

## How Odoo Handles Database Migrations

**Good News**: Odoo automatically creates database columns when you add fields to models. You just need to upgrade the module!

### Automatic Process

When you upgrade a module, Odoo:

1. Reads your Python model definitions
2. Compares with existing database schema
3. **Automatically adds missing columns** to database tables
4. Updates metadata in `ir_model_fields` table
5. Applies default values if specified

## Method 1: Upgrade Module (Automatic Migration) ✅ RECOMMENDED

### Via Command Line:

```powershell
# Make sure Odoo server is STOPPED first
python odoo-bin -c odoo.conf -u menu_management --stop-after-init
```

This will:

- ✅ Create new database columns for all new fields
- ✅ Create new tables for new models (like `menu_allergen`, `menu_dietary_tag`)
- ✅ Update database metadata
- ✅ Apply any default values

### Via Odoo UI:

1. Go to **Apps** menu
2. Remove filter "Apps" if active
3. Search for **"Menu Management"**
4. Click on the module
5. Click **"Upgrade"** button

⚠️ **Important**: After UI upgrade, you MUST restart Odoo server for model changes to take effect!

## Method 2: Verify Fields Were Added

### Check Database Directly (PostgreSQL):

```sql
-- Connect to your database
psql -U odoo_super -d odoo19

-- List all columns in menu_item table
\d menu_item

-- Or query column names
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'menu_item'
ORDER BY ordinal_position;
```

### Check via Odoo UI:

1. Enable **Developer Mode**:

   - Go to Settings → Activate Developer Mode

2. Check Model Fields:

   - Go to Settings → Technical → Database Structure → Models
   - Search for `menu.item`
   - Click on it to see all fields

3. Check in Your Module:
   - Go to Menu Management → Menu Items
   - Create/Edit a menu item
   - Verify new fields appear

## Method 3: Manual SQL Migration (Advanced - Not Usually Needed)

⚠️ **Only use this if automatic upgrade fails or you need custom migration logic**

### Create a Migration Script:

File: `addons/menu_management/migrations/1.1.0/post-migration.py`

```python
# -*- coding: utf-8 -*-

def migrate(cr, version):
    """Add new columns manually if needed"""

    # Add a column if it doesn't exist
    cr.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'menu_item' AND column_name = 'cost_price'
    """)

    if not cr.fetchone():
        cr.execute("""
            ALTER TABLE menu_item
            ADD COLUMN cost_price NUMERIC
        """)

    # Add other columns similarly
    # ...
```

### But Odoo handles this automatically! Only use manual SQL if:

- You need data transformation during migration
- You're renaming fields
- You need custom indexes
- Automatic upgrade failed

## Common Issues & Solutions

### Issue 1: Fields not appearing after upgrade

**Symptoms**: Upgraded module but fields not visible

**Solution**:

```powershell
# 1. Restart Odoo server completely
# 2. Clear browser cache (Ctrl+Shift+Delete)
# 3. Or use: --update-all flag
python odoo-bin -c odoo.conf -u all --stop-after-init
```

### Issue 2: "Column already exists" error

**Symptoms**: Database column exists but Odoo doesn't recognize it

**Solution**:

```sql
-- Check if field metadata exists
SELECT * FROM ir_model_fields
WHERE model = 'menu.item' AND name = 'cost_price';

-- If missing, you may need to:
-- 1. Drop the column manually
ALTER TABLE menu_item DROP COLUMN IF EXISTS cost_price;
-- 2. Upgrade module again
```

### Issue 3: Foreign key constraints fail

**Symptoms**: Error about missing UoM or other relations

**Solution**:

```powershell
# Make sure dependencies are installed first
# In your case: uom module must be installed
python odoo-bin -c odoo.conf -i uom --stop-after-init
python odoo-bin -c odoo.conf -u menu_management --stop-after-init
```

### Issue 4: Computed fields not working

**Symptoms**: Computed fields show 0 or empty

**Solution**:

```python
# In Odoo shell or via code, trigger recompute:
menu_items = env['menu.item'].search([])
menu_items._compute_total_time()  # Force recompute
```

## Step-by-Step Migration Checklist

- [ ] **Backup your database** (always!)
- [ ] **Stop Odoo server**
- [ ] **Upgrade module**: `python odoo-bin -c odoo.conf -u menu_management --stop-after-init`
- [ ] **Check logs** for errors
- [ ] **Restart Odoo**: `python odoo-bin -c odoo.conf`
- [ ] **Clear browser cache**
- [ ] **Verify fields** in form view
- [ ] **Check database** directly if needed

## Quick Verification Commands

```powershell
# 1. Check if upgrade completed
python odoo-bin -c odoo.conf -u menu_management --stop-after-init --log-level=info

# 2. Check Odoo logs for errors
Get-Content odoo.log -Tail 50

# 3. Verify in PostgreSQL (if you have psql)
psql -U odoo_super -d odoo19 -c "\d menu_item"
```

## What Gets Created Automatically

For each new field, Odoo creates:

1. **Database Column**:

   - `Char` → `VARCHAR`
   - `Integer` → `INTEGER`
   - `Float` → `NUMERIC`
   - `Boolean` → `BOOLEAN`
   - `Text` → `TEXT`
   - `Date` → `DATE`
   - `Datetime` → `TIMESTAMP`
   - `Image` → `BYTEA` (binary)

2. **Many2one fields**:

   - Column: `uom_id` (INTEGER, foreign key)
   - Foreign key constraint to `uom_uom` table

3. **Many2many fields**:

   - New relation table: `menu_item_allergen_rel`
   - Columns: `menu_item_id`, `allergen_id`

4. **One2many fields**:

   - No new column (stored on related model)

5. **Computed fields**:
   - Usually `store=False` (not in DB)
   - Or `store=True` (column created, updated by compute function)

## Summary

✅ **For normal field additions**: Just upgrade the module - Odoo handles everything!

✅ **After upgrade**: Restart server and clear browser cache

✅ **To verify**: Check the model form view or query database directly

❌ **Don't manually create columns** unless you have a specific reason

The upgrade command handles all database schema changes automatically!

