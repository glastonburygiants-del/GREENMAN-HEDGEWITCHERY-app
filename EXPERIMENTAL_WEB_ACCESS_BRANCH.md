# GREENMAN Experimental Web & Access Branch

This branch is the starting point for the new experimental Greenman versions.

## Base
Created from the working `main` branch at FV3.4 (`Build FV3.4 first-install country gate`).

## Golden rule
DO NOT make experimental access, key-generator, subscription, web-app, or entitlement changes directly on `main`.

The existing working app on `main` must remain untouched unless the owner explicitly decides that a tested experimental change is ready to be promoted later.

## Experimental scope
Work on this branch may include:
- Android Admin-only access-key generator
- Supabase key/entitlement validation
- Android special-access redemption
- Future Google Play one-time Full Greenman entitlement
- Future PayPal web subscription entitlement
- Future browser/web-app version of Greenman
- Customer-facing web access-code redemption

## Admin boundary
The Admin/Master area and key generator remain Android-app only.

The website/web app must NOT contain:
- Greenman Admin pages
- Key generator UI
- Master PIN UI
- privileged Supabase credentials
- service-role keys

The web app may only expose customer login/subscription and customer access-code redemption.

## Release approach
Experimental builds should be versioned independently from the existing working app so they can be tested without replacing the stable baseline.

Do not merge this branch into `main` automatically.
