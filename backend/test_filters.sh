#!/bin/bash
# Filter Logic Testing Commands for RushJob
# Run these after deploying the updated company list

echo "🧪 RUSHJOB FILTER LOGIC TESTING"
echo "=" * 50

# First, seed the new companies and poll
echo "1. Seeding new companies..."
curl -X POST https://rushjob-production.up.railway.app/api/v1/companies/seed

echo -e "\n2. Polling all companies..."
curl -X POST https://rushjob-production.up.railway.app/api/v1/poll-now | jq '.stats'

echo -e "\n🔍 TESTING LOCATION MATCHING"
echo "=" * 30

# Test complex location parsing from real Stripe data
echo "3. Complex location jobs (should have Seattle, SF, Remote):"
curl "https://rushjob-production.up.railway.app/api/v1/jobs?company_slugs=stripe&limit=5" | jq '.[] | {title, location}' | head -10

echo -e "\n4. Remote jobs across all companies:"
curl "https://rushjob-production.up.railway.app/api/v1/jobs?limit=20" | jq '.[] | select(.location | test("remote"; "i")) | {title, location, company_id}' | head -10

echo -e "\n🎯 TESTING KEYWORD MATCHING"
echo "=" * 30

# Test keyword searches
echo "5. Engineer jobs:"
curl "https://rushjob-production.up.railway.app/api/v1/jobs?limit=50" | jq '.[] | select(.title | test("engineer"; "i")) | {title, company_id}' | head -5

echo -e "\n6. Senior roles:"
curl "https://rushjob-production.up.railway.app/api/v1/jobs?limit=50" | jq '.[] | select(.title | test("senior"; "i")) | {title, company_id}' | head -5

echo -e "\n📊 TESTING DATA QUALITY"
echo "=" * 30

# Test data parsing quality
echo "7. Job type distribution:"
curl "https://rushjob-production.up.railway.app/api/v1/jobs?limit=100" | jq '.[] | .job_type' | sort | uniq -c

echo -e "\n8. Department distribution:"
curl "https://rushjob-production.up.railway.app/api/v1/jobs?limit=100" | jq '.[] | .department' | sort | uniq -c | head -10

echo -e "\n9. Location variety:"
curl "https://rushjob-production.up.railway.app/api/v1/jobs?limit=100" | jq '.[] | .location' | sort | uniq -c | head -15

echo -e "\n✅ Filter testing complete!"
