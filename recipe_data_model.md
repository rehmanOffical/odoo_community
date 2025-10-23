# Odoo Recipe Data Model Flow for Catering

## Overview

A recipe in Odoo catering system is stored as a Bill of Materials (BoM). The BoM data model defines what ingredients are needed, in what quantities, and how they relate to the final product. This document describes the complete data structure and flow.

---

## Core Data Models

### 1. Product (product.product / product.template)

This represents a catering dish or product.

**Key Fields:**
- id: Unique product identifier
- name: Product name (e.g., "Biryani for 10 people")
- type: Product type (set to "consu" for food)
- uom_id: Unit of measure (e.g., "portions", "kg")
- list_price: Selling price
- cost_price: Cost to make
- description: Product description
- image: Product image
- categ_id: Product category (Appetizer, Main, Dessert)

**Catering Fields (Custom):**
- servings_per_unit: How many people this dish serves
- prep_time: Preparation time in minutes
- cooking_time: Cooking time in minutes
- total_time: Total time = prep_time + cooking_time
- difficulty_level: Easy, Medium, Complex
- allergen_tags: Many2Many relation to allergens
- required_equipment: Many2Many relation to equipment needed
- food_safety_notes: Special food handling instructions

**Database Table:** product_product, product_template

---

### 2. Bill of Materials (mrp.bom)

This is the recipe definition. It links a product to all ingredients needed.

**Key Fields:**
- id: Unique BoM identifier
- name: BoM name (e.g., "Biryani Recipe v1.0")
- product_id: Link to product (foreign key to product.product)
- product_qty: Quantity of main product (always 1 for recipes)
- product_uom_id: Unit of main product
- type: BoM type ("normal" for most recipes)
- sequence: Order in system
- active: Whether BoM is active or archived

**Catering Fields (Custom):**
- prep_time: Preparation time in minutes
- cooking_time: Cooking time in minutes
- difficulty_level: Easy, Medium, Complex
- ingredients_count: Count of ingredients in recipe
- version: Recipe version number
- is_active_recipe: Boolean to mark if currently used
- recipe_notes: Special instructions or notes
- created_date: When recipe was created
- last_modified_date: When recipe was last changed

**Database Table:** mrp_bom

**Relationships:**
- Has many BoM lines (one-to-many relation to mrp.bom.line)
- Links to one product (many-to-one relation to product.product)

---

### 3. Bill of Materials Line (mrp.bom.line)

Each line represents one ingredient in the recipe.

**Key Fields:**
- id: Unique line identifier
- bom_id: Link to parent BoM (foreign key to mrp.bom)
- product_id: Link to ingredient product (foreign key to product.product)
- product_qty: Quantity of ingredient needed
- product_uom_id: Unit of measure for ingredient
- sequence: Order of ingredients in recipe
- operation_id: Link to production step (optional)

**Catering Fields (Custom):**
- ingredient_cost: Cost of this ingredient
- ingredient_supplier: Which supplier provides this ingredient
- is_optional: Whether this ingredient is optional
- notes: Special notes about this ingredient (e.g., "Add at the end")
- can_substitute: Whether this ingredient can be substituted
- substitute_product_id: Alternative product if available

**Database Table:** mrp_bom_line

**Relationships:**
- Links to parent BoM (many-to-one to mrp.bom)
- Links to ingredient product (many-to-one to product.product)

---

### 4. Product Supplier (product.supplierinfo)

Links products to their suppliers for purchasing.

**Key Fields:**
- id: Unique identifier
- product_tmpl_id: Link to product template
- partner_id: Link to supplier
- product_code: Supplier's product code
- product_name: Supplier's product name
- min_qty: Minimum order quantity
- price: Unit price from this supplier
- currency_id: Currency of price
- delay: Delivery lead time in days
- active: Whether supplier is active

**Database Table:** product_supplierinfo

**Relationships:**
- Links to product template (many-to-one)
- Links to supplier/partner (many-to-one)

---

## Complete Recipe Data Structure

```
PRODUCT (Dish)
├── id: 1
├── name: "Biryani"
├── type: "consu"
├── servings_per_unit: 10
├── prep_time: 30 (minutes)
├── cooking_time: 45 (minutes)
├── total_time: 75 (minutes)
├── difficulty_level: "medium"
├── list_price: 5000 (price for 10 people)
│
└──(Recipe)
    ├── id: 5
    ├── name: "Biryani Recipe v1.0"
    ├── product_id: 1 (link to Biryani product)
    ├── product_qty: 1
    ├── prep_time: 30
    ├── cooking_time: 45
    │
    └──(Ingredients)
        │
        ├── Line 1: Rice
        │   ├── product_id: 101 (link to Rice product)
        │   ├── product_qty: 5
        │   ├── product_uom_id: "kg"
        │   ├── ingredient_supplier: "Rice Supplier A"
        │   └── ingredient_cost: 250
        │
        ├── Line 2: Chicken
        │   ├── product_id: 102 (link to Chicken product)
        │   ├── product_qty: 2
        │   ├── product_uom_id: "kg"
        │   ├── ingredient_supplier: "Meat Supplier B"
        │   └── ingredient_cost: 600
        │
        ├── Line 3: Spices Mix
        │   ├── product_id: 103 (link to Spices product)
        │   ├── product_qty: 0.5
        │   ├── product_uom_id: "kg"
        │   ├── ingredient_supplier: "Spice Supplier C"
        │   └── ingredient_cost: 150
        │
        └── Line 4: Ghee
            ├── product_id: 104 (link to Ghee product)
            ├── product_qty: 0.5
            ├── product_uom_id: "liter"
            ├── ingredient_supplier: "Dairy Supplier D"
            └── ingredient_cost: 400
```

---

## Data Flow: From Recipe to Sales Order

### Step 1: Recipe Created in System

```
Create BoM (Recipe)
├── Select Product: Biryani
├── Add Ingredients:
│   ├── Rice: 5 kg
│   ├── Chicken: 2 kg
│   ├── Spices: 0.5 kg
│   └── Ghee: 0.5 liter
└── Save Recipe
```

---

### Step 2: Customer Places Order

```
Customer Order
├── Product: Biryani
├── Quantity: 3 (3 portions of 10 people each = 30 people)
└── Order Date: 2025-01-15
```

---

### Step 3: System Fetches Recipe and Calculates Ingredients

```
Catering Order Flow Module Processing

Fetch Recipe BoM for Biryani
├── Find BoM record with product_id = Biryani
├── Read all BoM lines from this BoM
│
Calculate Ingredient Quantities:
├── For each BoM line:
│   └── Ingredient Quantity = BOM_LINE.product_qty × ORDER_QUANTITY
│
├── Rice: 5 kg × 3 = 15 kg
├── Chicken: 2 kg × 3 = 6 kg
├── Spices: 0.5 kg × 3 = 1.5 kg
└── Ghee: 0.5 liter × 3 = 1.5 liter

Total Ingredients Needed for Order:
├── Rice: 15 kg
├── Chicken: 6 kg
├── Spices: 1.5 kg
└── Ghee: 1.5 liter
```

---

### Step 4: Create Purchase Orders

```
For Each Ingredient:
├── Find Supplier from BOM_LINE.ingredient_supplier
│
├── Rice (15 kg)
│   └── Create PO to Rice Supplier A
│       ├── Product: Rice
│       ├── Quantity: 15 kg
│       └── Unit Price: 50 per kg = 750 total
│
├── Chicken (6 kg)
│   └── Create PO to Meat Supplier B
│       ├── Product: Chicken
│       ├── Quantity: 6 kg
│       └── Unit Price: 300 per kg = 1800 total
│
├── Spices (1.5 kg)
│   └── Create PO to Spice Supplier C
│       ├── Product: Spices
│       ├── Quantity: 1.5 kg
│       └── Unit Price: 300 per kg = 450 total
│
└── Ghee (1.5 liter)
    └── Create PO to Dairy Supplier D
        ├── Product: Ghee
        ├── Quantity: 1.5 liter
        └── Unit Price: 800 per liter = 1200 total

Total Ingredient Cost: 750 + 1800 + 450 + 1200 = 4200
```

---

### Step 5: Schedule Cooking on Calendar

```
Calculate Cooking Start Time:
├── Order Ready Date: 2025-01-15
├── Cooking Time from BoM: 45 minutes
├── Prep Time from BoM: 30 minutes
├── Total Time: 75 minutes
│
Cooking Start Time = 2025-01-15 - 75 minutes
                   = 2025-01-15 at (delivery_time - 1 hour 15 minutes)

Example: If delivery is 6:00 PM
         Cooking starts at 4:45 PM

Reserve Calendar:
├── Chef: Assigned Chef
├── Start Time: 4:45 PM
├── End Time: 6:00 PM
├── Task: Cook Biryani (3 portions)
└── Equipment: Cooking vessels, stove
```

---

### Step 6: Create Manufacturing Order

```
Manufacturing Order Created:
├── id: 1001
├── product_id: Biryani
├── product_qty: 3
├── bom_id: 5 (link to recipe)
├── source_document: SO/2025/001 (link to sales order)
├── state: confirmed
│
BOM Components Auto-Populated:
├── Rice: 15 kg (calculated)
├── Chicken: 6 kg (calculated)
├── Spices: 1.5 kg (calculated)
└── Ghee: 1.5 liter (calculated)

Work Orders Created:
└── One work order per ingredient
    ├── Pick Rice: 15 kg
    ├── Pick Chicken: 6 kg
    ├── Pick Spices: 1.5 kg
    └── Pick Ghee: 1.5 liter
```

---

### Step 7: Goods Receipt

```
When Supplier Delivers:
│
Goods Receipt Record:
├── Source: Purchase Order
├── Product: Rice
├── Quantity Ordered: 15 kg
├── Quantity Received: 15 kg
├── Date Received: 2025-01-14
├── Status: Received
│
Inventory Updated:
├── Stock Location: Kitchen Storage
├── Rice Stock: +15 kg
├── Quality Check: Pass
└── Ready for Cooking
```

---

### Step 8: Production and Inventory Deduction

```
Cooking Process:
│
As Chef Uses Ingredients:
├── Pick Rice: 15 kg from stock
│   └── Stock: Rice 0 kg (15 - 15 = 0)
│
├── Pick Chicken: 6 kg from stock
│   └── Stock: Chicken 0 kg (6 - 6 = 0)
│
├── Pick Spices: 1.5 kg from stock
│   └── Stock: Spices 0 kg (1.5 - 1.5 = 0)
│
└── Pick Ghee: 1.5 liter from stock
    └── Stock: Ghee 0 liter (1.5 - 1.5 = 0)

Manufacturing Order Status: Completed
Product Produced: 3 portions of Biryani (30 people)
```

---

## Recipe Data Relationships

```
PRODUCT ──────────┐
(Dish)            │
  ├── name        │
  ├── price       │
  └── details     │
                  │ 1:Many
                  ↓
        BOM (Recipe)
        ├── id
        ├── name
        ├── product_id ──→ PRODUCT
        └── lines
              │ 1:Many
              ↓
        BOM LINE (Ingredient)
        ├── product_id ──→ PRODUCT (Ingredient)
        ├── product_qty
        ├── supplier_id ──→ SUPPLIER
        └── cost


SALES ORDER
├── product_id ──→ PRODUCT
├── quantity: 3
│
└── Catering Order Flow
    ├── Fetch BOM from product
    ├── Multiply quantities
    ├── Create PURCHASE ORDERS
    ├── Schedule CALENDAR
    └── Create MFG ORDER
```

---

## Key Database Tables

| Table | Purpose | Key Fields |
|---|---|---|
| product_product | Individual product variants | id, name, type, uom_id |
| product_template | Product group | id, name, category_id |
| mrp_bom | Recipe definition | id, product_id, product_qty |
| mrp_bom_line | Recipe ingredients | id, bom_id, product_id, product_qty |
| product_supplierinfo | Supplier info | id, product_id, partner_id, price |
| sale_order | Customer order | id, product_id, product_qty |
| purchase_order | Supplier order | id, product_id, product_qty |
| mrp_production | Manufacturing order | id, bom_id, product_qty |
| stock_move | Inventory movement | id, product_id, quantity |

---

## Data Validation Rules

### When Creating BoM (Recipe)

- Product type must be "consu" (consumable)
- At least one ingredient line must exist
- All ingredient quantities must be greater than zero
- All ingredients must have valid units of measure
- Supplier must be configured for each ingredient

### When Processing Sales Order

- Product must have an active BoM (recipe)
- All ingredients must be available or ordered
- Cooking time must be valid
- Delivery time must be in future
- Kitchen calendar must have available slots

### When Creating Purchase Order

- Supplier must be configured for ingredient
- Order quantity must be greater than zero
- Delivery date must be before cooking start date
- Supplier must have minimum order quantity met

---

## Custom Fields Summary

**On Product (product.product):**
- servings_per_unit
- prep_time_minutes
- cooking_time_minutes
- total_time_minutes
- difficulty_level
- allergen_tags
- required_equipment

**On BoM (mrp.bom):**
- prep_time_minutes
- cooking_time_minutes
- difficulty_level
- ingredients_count
- version
- is_active_recipe

**On BoM Line (mrp.bom.line):**
- ingredient_supplier
- ingredient_cost
- is_optional
- can_substitute
- substitute_product_id