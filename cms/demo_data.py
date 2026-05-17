"""
Demo data for Services and SubServices, aligned with design/src/data (servicesData.ts, subServicesData.ts).
Used by seed_demo to populate full content for service and sub-service pages.
"""
# DEMO_SERVICES and DEMO_SUB_SERVICES_FULL are populated by seed_demo from design data.
# Structure: DEMO_SERVICES = list of dicts with slug, title, short_title, tagline, description,
# long_description, starting_price, timeline, offer_badge, category, benefits[], required_documents[],
# process_steps[], deliverables[], price_tiers[], faqs[], target_users[], meta_*, sub_services[].
# DEMO_SUB_SERVICES_FULL = list of dicts with parent_slug, slug, title, tagline, description,
# long_description, starting_price, timeline, offer_badge, benefits[], required_documents[],
# process_steps[] (with optional documents[]), deliverables[], price_tiers[], eligibility[], faqs[], meta_*.

from .demo_services_content import DEMO_SERVICES, DEMO_SUB_SERVICES_FULL

__all__ = ["DEMO_SERVICES", "DEMO_SUB_SERVICES_FULL"]
