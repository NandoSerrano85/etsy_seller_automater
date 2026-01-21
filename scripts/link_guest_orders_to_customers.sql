-- Diagnostic: Find orders that might need linking
-- Run this to see the current state of orders

-- 1. Show all orders with their customer info
SELECT
    o.order_number,
    o.customer_id,
    o.guest_email,
    o.created_at,
    c.email as customer_email,
    c.first_name,
    c.last_name
FROM ecommerce_orders o
LEFT JOIN ecommerce_customers c ON o.customer_id = c.id
ORDER BY o.created_at DESC
LIMIT 20;

-- 2. Find guest orders that match existing customer emails
SELECT
    o.order_number,
    o.guest_email,
    o.customer_id as current_customer_id,
    c.id as matching_customer_id,
    c.email as customer_email
FROM ecommerce_orders o
JOIN ecommerce_customers c ON LOWER(o.guest_email) = LOWER(c.email)
WHERE o.customer_id IS NULL
  AND o.guest_email IS NOT NULL;

-- 3. FIX: Link guest orders to their matching customers by email
-- UNCOMMENT TO RUN:
/*
UPDATE ecommerce_orders o
SET customer_id = c.id
FROM ecommerce_customers c
WHERE LOWER(o.guest_email) = LOWER(c.email)
  AND o.customer_id IS NULL
  AND o.guest_email IS NOT NULL;
*/

-- 4. Check a specific customer's orders (replace with actual email)
-- SELECT
--     o.order_number,
--     o.customer_id,
--     o.guest_email,
--     o.total,
--     o.status,
--     o.created_at
-- FROM ecommerce_orders o
-- WHERE o.guest_email = 'customer@example.com'
--    OR o.customer_id = (SELECT id FROM ecommerce_customers WHERE email = 'customer@example.com')
-- ORDER BY o.created_at DESC;
