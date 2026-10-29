"""Sample approved sources for a fictional invoicing brand, Ledgerly."""

SAMPLES = [
    {
        "id": "case_study",
        "label": "Case study",
        "source_type": "case_study",
        "title": "How Kavya Interiors cut late payments by 41% in one quarter",
        "url": "https://ledgerly.example/customers/kavya-interiors",
        "brand": {
            "brand_name": "Ledgerly",
            "preset": "expert",
            "banned_words": "cheap, guarantee",
            "preferred_terms": "customers -> clients\nsoftware -> platform",
            "hashtags": "#Ledgerly",
            "cta": "Read the full case study",
        },
        "source_text": """Kavya Interiors is a 14-person design studio in Ahmedabad that handles around 60 residential projects a year.

## The challenge
Until 2025, the studio sent every invoice by hand from a spreadsheet. Its founder, Kavya Mehta, spent close to 9 hours a week chasing payments over phone and WhatsApp. Average payment time had stretched to 38 days, and two large projects were paused because cash was tied up in unpaid bills.

## What they changed
In January 2026 the studio moved its invoicing to Ledgerly. Every project now has a payment schedule linked to its milestones. Reminders go out automatically 3 days before and 2 days after each due date, and customers can pay by UPI straight from the invoice.

The team also started sending a single-page project summary with each invoice, so customers know exactly what they are paying for.

## The results
Within one quarter, late payments fell by 41%. Average payment time dropped from 38 days to 22 days. Kavya now spends under 2 hours a week on collections. "I used to dread the end of the month. Now the reminders do the awkward part for me," she says.

The studio has used the freed-up cash to take on 8 more projects this year without adding staff.""",
    },
    {
        "id": "blog",
        "label": "Blog post",
        "source_type": "blog",
        "title": "Why late payments hurt small agencies more than big ones",
        "url": "https://ledgerly.example/blog/late-payments-small-agencies",
        "brand": {
            "brand_name": "Ledgerly",
            "preset": "friendly",
            "banned_words": "cheap, guarantee",
            "preferred_terms": "customers -> clients",
            "hashtags": "#Ledgerly #SmallBusiness",
            "cta": "Read the full article",
        },
        "source_text": """Why late payments hurt small agencies more than big ones

A large firm can absorb a client who pays 60 days late. A five-person agency usually cannot. When we surveyed 412 small agencies on Ledgerly in 2026, 63% said late payments had forced them to delay paying their own suppliers at least once in the past year.

The problem is not just the money. It is the time spent chasing it. The agencies in our survey spent an average of 6 hours a week following up on unpaid invoices. That is almost a full working day lost every week.

There are three habits that make the biggest difference. First, agree on payment terms before the work starts and put them on every invoice. Second, send the invoice the day the milestone is delivered, not at the end of the month. Third, make paying easy, because every extra step gives a client a reason to wait.

Agencies that invoiced on delivery were paid 11 days faster on average than those that batched invoices monthly. Small changes in timing add up quickly.

Late payment is common, but it is not inevitable. Clear terms, quick invoices and easy payment options put you back in control of your cash flow.""",
    },
    {
        "id": "product_page",
        "label": "Product page",
        "source_type": "product_page",
        "title": "Ledgerly Reminders",
        "url": "https://ledgerly.example/reminders",
        "brand": {
            "brand_name": "Ledgerly",
            "preset": "bold",
            "banned_words": "cheap, guarantee, revolutionary",
            "preferred_terms": "customers -> clients",
            "hashtags": "#Ledgerly",
            "cta": "See how Reminders works",
        },
        "source_text": """Ledgerly Reminders

Get paid on time without writing a single follow-up email. Ledgerly Reminders sends polite, scheduled nudges to your customers so you never have to chase an invoice again.

## Features
- Set a reminder schedule once and apply it to every invoice automatically.
- Choose from 5 tone templates, from a gentle nudge to a firm final notice.
- Reminders go out by email and WhatsApp, with a UPI payment link in every message.
- See who opened each reminder and who has paid, all on one dashboard.
- Pause reminders for a client with one click when you are already in touch.

## Why it matters
Businesses using Reminders get paid an average of 12 days sooner. Most teams save around 5 hours a week that used to go into follow-ups.

Reminders is included in every Ledgerly plan at no extra cost. Set it up in under 10 minutes and let it run in the background.""",
    },
]
