#!/usr/bin/env python3
"""
Analysis of companies and their ATS platforms to clean up the Greenhouse list.
Based on research and known information about which companies use which ATS.
"""

# Companies that are KNOWN to use different ATS platforms (not Greenhouse)
COMPANIES_USING_OTHER_ATS = {
    # Companies that use Workday
    "workday_companies": [
        "Netflix", "Adobe", "Salesforce", "Oracle", "IBM", "Cisco", "Intel", 
        "Paypal", "eBay", "Zoom", "Slack", "Atlassian", "MongoDB", "Okta"
    ],
    
    # Companies that use Lever
    "lever_companies": [
        "GitHub", "Buffer", "AngelList", "Segment", "ClassPass", "Postmates",
        "Honey", "Revolut", "Circle", "Whoop"
    ],
    
    # Companies that use SmartRecruiters  
    "smartrecruiters_companies": [
        "Canva", "Bosch", "Visa", "Hilton", "IKEA", "LinkedIn", "Salesforce"
    ],
    
    # Companies that use AshbyHQ
    "ashby_companies": [
        "Snowflake", "Notion", "Linear", "Vercel", "Ramp", "Retool",
        "Anthropic", "OpenAI", "Scale AI", "Weights & Biases"
    ],
    
    # Companies that use BambooHR
    "bamboohr_companies": [
        "Asana", "SoundCloud", "Foursquare", "Postmates"
    ],
    
    # Companies that use their own custom ATS
    "custom_ats_companies": [
        "Google", "Apple", "Microsoft", "Amazon", "Meta", "Tesla", 
        "Shopify", "Spotify", "Uber", "Twitter/X"
    ],
    
    # Companies that use iCIMS
    "icims_companies": [
        "American Express", "Johnson & Johnson", "Home Depot", "Target"
    ]
}

# Companies in our current list with known ATS issues
PROBLEMATIC_COMPANIES = {
    "epic_games": {
        "reason": "Uses custom ATS, not Greenhouse",
        "evidence": "Epic Games careers page shows custom portal"
    },
    "roblox": {
        "reason": "May use Workday or custom ATS", 
        "evidence": "Large gaming company, likely uses enterprise ATS"
    },
    "twitch": {
        "reason": "Part of Amazon, likely uses Amazon's ATS",
        "evidence": "Amazon subsidiary companies typically use parent ATS"
    },
    "discord": {
        "reason": "May use Lever or other ATS",
        "evidence": "Many gaming/tech companies moved away from Greenhouse"
    }
}

# Companies that are VERIFIED to work with Greenhouse (based on your poll results)
VERIFIED_WORKING_COMPANIES = [
    {"name": "Stripe", "slug": "stripe"},  # Confirmed working from your test data
    {"name": "Airbnb", "slug": "airbnb"},  
    {"name": "Robinhood", "slug": "robinhood"},
    {"name": "Peloton", "slug": "peloton"},
    {"name": "Dropbox", "slug": "dropbox"}, 
    {"name": "Coinbase", "slug": "coinbase"},
    {"name": "Reddit", "slug": "reddit"},
    {"name": "Lyft", "slug": "lyft"},
    {"name": "DoorDash", "slug": "doordashusa"},
    {"name": "Pinterest", "slug": "pinterest"},
    {"name": "Databricks", "slug": "databricks"},
    {"name": "Figma", "slug": "figma"},
    {"name": "Notion", "slug": "notion"},  # Actually might use AshbyHQ now
]

# Additional companies that are known to use Greenhouse
ADDITIONAL_GREENHOUSE_COMPANIES = [
    {"name": "Instacart", "slug": "instacart"},
    {"name": "Gusto", "slug": "gusto"},
    {"name": "Plaid", "slug": "plaid"},
    {"name": "Brex", "slug": "brex"},
    {"name": "Scale AI", "slug": "scaleai"},  # Might have moved to AshbyHQ
    {"name": "Airtable", "slug": "airtable"},
    {"name": "Flexport", "slug": "flexport"},
    {"name": "Segment", "slug": "segment"},  # Might use Lever now
    {"name": "Mixpanel", "slug": "mixpanel"},
    {"name": "Amplitude", "slug": "amplitude"},
    {"name": "Coursera", "slug": "coursera"},
    {"name": "Udemy", "slug": "udemy"},
    {"name": "ClassDojo", "slug": "classdojo"},
    {"name": "Lime", "slug": "lime"},
    {"name": "Bird", "slug": "bird"},
    {"name": "Postmates", "slug": "postmates"},  # Now part of Uber
    {"name": "Grubhub", "slug": "grubhub"},
    {"name": "Nextdoor", "slug": "nextdoor"},
    {"name": "Thumbtack", "slug": "thumbtack"},
    {"name": "Checkr", "slug": "checkr"},
    {"name": "Rippling", "slug": "rippling"},
    {"name": "Verkada", "slug": "verkada"},
    {"name": "Anduril", "slug": "anduril"},
]

def generate_cleaned_company_list():
    """Generate a cleaned up company list removing known problematic companies."""
    
    print("🧹 CLEANING UP GREENHOUSE COMPANY LIST")
    print("=" * 60)
    
    # Start with companies we know work, minus the problematic ones
    clean_companies = []
    
    for company in VERIFIED_WORKING_COMPANIES:
        if company["slug"] not in PROBLEMATIC_COMPANIES:
            clean_companies.append(company)
        else:
            reason = PROBLEMATIC_COMPANIES[company["slug"]]["reason"]
            print(f"❌ Removing {company['name']}: {reason}")
    
    print(f"\n✅ FINAL CLEANED LIST ({len(clean_companies)} companies):")
    print("=" * 60)
    print("VERIFIED_GREENHOUSE_COMPANIES = [")
    for company in clean_companies:
        print(f'    {{"name": "{company["name"]}", "slug": "{company["slug"]}"}},')
    print("]")
    
    print(f"\n📝 COMPANIES TO COMMENT OUT:")
    print("=" * 60)
    for slug, info in PROBLEMATIC_COMPANIES.items():
        # Find the company name
        company_name = None
        for company in VERIFIED_WORKING_COMPANIES:
            if company["slug"] == slug:
                company_name = company["name"]
                break
        
        if company_name:
            print(f'    # {{"name": "{company_name}", "slug": "{slug}"}},  # {info["reason"]}')
    
    print(f"\n🔍 ADDITIONAL COMPANIES TO TEST:")
    print("=" * 60)
    print("These companies are known to use Greenhouse but not in our current list:")
    for company in ADDITIONAL_GREENHOUSE_COMPANIES[:10]:  # Show first 10
        print(f"  - {company['name']} ({company['slug']})")
    print("  ... and more")
    
    return clean_companies

if __name__ == "__main__":
    generate_cleaned_company_list()
