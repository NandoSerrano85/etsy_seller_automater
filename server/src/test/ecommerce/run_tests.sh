#!/bin/bash

# Ecommerce API Test Runner
# Run all ecommerce tests with detailed output

echo "========================================="
echo "  ECOMMERCE API TEST SUITE"
echo "========================================="
echo ""

# Set Python path to include server directory
export PYTHONPATH="/Users/fserrano/Documents/Projects/etsy_seller_automater:$PYTHONPATH"

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest is not installed. Installing..."
    pip install pytest pytest-cov
fi

# Set test environment variables
export JWT_SECRET_KEY="test-secret-key"
export STRIPE_SECRET_KEY="sk_test_fake_key_for_testing"

echo "Running all ecommerce tests..."
echo ""

# Run tests with detailed output
pytest server/src/test/ecommerce/ \
    -v \
    --tb=short \
    --color=yes \
    --durations=10 \
    -W ignore::DeprecationWarning

# Capture exit code
exit_code=$?

echo ""
echo "========================================="
if [ $exit_code -eq 0 ]; then
    echo "✅ ALL TESTS PASSED!"
else
    echo "❌ SOME TESTS FAILED"
fi
echo "========================================="

exit $exit_code
