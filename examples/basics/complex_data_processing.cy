# Debugged Complex E-commerce Order Processing System
# This version addresses common cy language limitations found during debugging
#
# NOTE: This example requires input data. To run with custom data:
# poetry run python -c "from cy_language import Cy; data = {...}; print(Cy().run(open('examples/advanced/complex_example_debugged.cy').read(), data))"

# Use input if provided, otherwise use sample data
input_data = input
if (input_data == null) {
    # Sample data for demonstration
    input_data = {
        "order": {
            "order_id": "ORD-12345",
            "items": [{"product_id": "PROD-001", "quantity": 3}]
        },
        "customer": {
            "name": "Alice Johnson",
            "email": "alice@example.com",
            "tier": "gold",
            "address": "123 Main St, City, State"
        },
        "inventory": {
            "PROD-001": {"name": "Premium Widget", "price": 49.99, "stock": 50}
        }
    }
}

# Input order data
order = input_data["order"]
customer = input_data["customer"]
inventory = input_data["inventory"]

# Initialize processing variables
order_valid = True
total_amount = 0

# Extract commonly used values to avoid nested interpolation issues
order_id = order["order_id"]
customer_name = customer["name"]
customer_email = customer["email"]
customer_tier = customer["tier"]
customer_address = customer["address"]

# Process first item (simplified for demonstration)
first_item = order["items"][0]
product_id = first_item["product_id"]
quantity = first_item["quantity"]

# Get product from inventory
product = inventory[product_id]
available_stock = product["stock"]
product_name = product["name"]
base_price = product["price"]

# Check stock availability
if (quantity > available_stock) {
    order_valid = False
    error_message = "Insufficient stock"
} else {
    # Calculate item pricing with clear intermediate steps
    item_subtotal = base_price * quantity

    # Apply bulk discounts
    discount_rate = 0
    if (quantity >= 10) {
        discount_rate = 0.1
    } elif (quantity >= 5) {
        discount_rate = 0.05
    }

    bulk_discount = item_subtotal * discount_rate

    # Apply customer tier discount
    tier_discount_rate = 0
    if (customer_tier == "premium") {
        tier_discount_rate = 0.15
    } elif (customer_tier == "gold") {
        tier_discount_rate = 0.1
    } elif (customer_tier == "silver") {
        tier_discount_rate = 0.05
    }

    after_bulk = item_subtotal - bulk_discount
    tier_discount_amount = after_bulk * tier_discount_rate
    final_item_price = after_bulk - tier_discount_amount

    total_amount = final_item_price
}

# Calculate shipping
shipping_cost = 5.00
free_shipping = customer_tier == "premium" and total_amount > 100
if (free_shipping) {
    shipping_cost = 0
}

final_total = total_amount + shipping_cost

# Status for display
status = order_valid and "APPROVED" or "REJECTED"

# Generate order summary using extracted variables to avoid nested interpolation
if (order_valid) {
    output = """
# Order Processing Complete

## Order Summary
- Order ID: ${order_id}
- Customer: ${customer_name} (${customer_email})
- Status: ${status}

## Product Details
- Product: ${product_name}
- Quantity: ${quantity}
- Base Price: $${base_price}
- Item Subtotal: $${item_subtotal}
- Bulk Discount Rate: ${discount_rate}
- Bulk Discount: $${bulk_discount}
- Tier Discount Rate: ${tier_discount_rate}
- Tier Discount: $${tier_discount_amount}
- Item Final Price: $${final_item_price}

## Financial Summary
- Subtotal: $${total_amount}
- Shipping: $${shipping_cost} (Free shipping: ${free_shipping})
- **Final Total: $${final_total}**

## Customer Details
- Tier: ${customer_tier}
- Address: ${customer_address}

## Processing Notes
- Complex nested object access works better with extracted variables
- String interpolation with nested objects like order["items"][0] can be problematic
- Boolean expressions work: Premium customer gets free shipping
- Mathematical calculations work correctly with proper operator precedence

*Order processed successfully and ready for fulfillment.*
"""
} else {
    output = """
# Order Processing Failed

## Order Summary
- Order ID: ${order_id}
- Customer: ${customer_name} (${customer_email})
- Status: ${status}

## Error Details
Product: ${product_name}
${error_message}
- Requested Quantity: ${quantity}
- Available Stock: ${available_stock}

## Resolution Required
Please adjust the quantity or wait for restocking.

*Order cannot be processed in current state.*
"""
}
return output
