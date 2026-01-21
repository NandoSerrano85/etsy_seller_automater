-- ============================================
-- Subscription User ID Fix Script
-- ============================================

-- STEP 1: Diagnose - View all users and their subscriptions
-- ============================================
SELECT
    u.id AS user_id,
    u.email,
    u.subscription_plan AS user_table_plan,
    s.id AS subscription_id,
    s.user_id AS subscription_user_id,
    s.tier AS subscription_tier,
    s.status AS subscription_status,
    CASE
        WHEN s.id IS NULL THEN 'NO SUBSCRIPTION RECORD'
        WHEN u.id = s.user_id THEN 'MATCH'
        ELSE 'MISMATCH'
    END AS status
FROM users u
LEFT JOIN subscriptions s ON u.id = s.user_id
ORDER BY u.email;

-- STEP 2: Find orphaned subscriptions (subscriptions with no matching user)
-- ============================================
SELECT
    s.*,
    'ORPHANED - No matching user' AS issue
FROM subscriptions s
LEFT JOIN users u ON s.user_id = u.id
WHERE u.id IS NULL;

-- STEP 3: Find users without subscriptions
-- ============================================
SELECT
    u.id,
    u.email,
    u.subscription_plan,
    'NO SUBSCRIPTION RECORD' AS issue
FROM users u
LEFT JOIN subscriptions s ON u.id = s.user_id
WHERE s.id IS NULL;

-- ============================================
-- FIX OPTIONS (Uncomment and modify as needed)
-- ============================================

-- OPTION A: If you have a specific user that needs a subscription created
-- Replace the values with your actual data
-- ============================================
/*
INSERT INTO subscriptions (id, user_id, tier, status, created_at, updated_at)
VALUES (
    gen_random_uuid(),
    'YOUR-USER-UUID-HERE',  -- Get this from: SELECT id FROM users WHERE email = 'your@email.com'
    'pro',                   -- The tier you want: 'free', 'starter', 'pro', 'full'
    'active',
    NOW(),
    NOW()
);
*/

-- OPTION B: If subscription exists but has wrong user_id, update it
-- ============================================
/*
UPDATE subscriptions
SET user_id = 'CORRECT-USER-UUID-HERE'
WHERE id = 'SUBSCRIPTION-UUID-HERE';
*/

-- OPTION C: Create subscriptions for all users who don't have one
-- Uses the user's subscription_plan field as the tier
-- ============================================
/*
INSERT INTO subscriptions (id, user_id, tier, status, created_at, updated_at)
SELECT
    gen_random_uuid(),
    u.id,
    COALESCE(u.subscription_plan, 'free'),
    'active',
    NOW(),
    NOW()
FROM users u
LEFT JOIN subscriptions s ON u.id = s.user_id
WHERE s.id IS NULL;
*/

-- OPTION D: Update subscription tier for a specific user
-- ============================================
/*
UPDATE subscriptions
SET tier = 'pro', updated_at = NOW()
WHERE user_id = (SELECT id FROM users WHERE email = 'your@email.com');
*/

-- OPTION E: Sync subscription tier from user's subscription_plan
-- (Updates existing subscriptions to match user table)
-- ============================================
/*
UPDATE subscriptions s
SET tier = u.subscription_plan, updated_at = NOW()
FROM users u
WHERE s.user_id = u.id
AND s.tier != u.subscription_plan;
*/
