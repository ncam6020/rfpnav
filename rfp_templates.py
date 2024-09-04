# rfp_templates.py

def get_rfp_pipeline_template(extracted_text):
    pipeline_template = f"""
    Extract and present the following key data points from this RFP document in a table format for CRM entry:
    - Client Name
    - Opportunity Name
    - Primary Contact (name, title, email, and phone)
    - Primary Practice (select from: Branded Environments, Corporate and Commercial, Corporate Interiors, Cultural and Civic, Health, Higher Education, Hospitality, K-12 Education, Landscape Architecture, Planning & Strategies, Science and Technology, Single Family Residential, Sports Recreation and Entertainment, Transportation, Urban Design, Unknown / Other)
    - Discipline (select from: Arch/Interior Design, Urban Design, Landscape Arch, Advisory Services, Branded Environments, Unknown / Other)
    - City
    - State / Province
    - Country
    - RFP Release Date
    - Proposal Due Date
    - Interview Date
    - Selection Date
    - Design Start Date
    - Design Completion Date
    - Construction Start Date
    - Construction Completion Date
    - Project Description (concise one sentence description)
    - Scope(s) of Work (select from: New, Renovation, Addition, Building Repositioning, Competition, Infrastructure, Master Plan, Planning, Programming, Replacement, Study, Unknown / Other)
    - Program Type(s) (select from: Civic and Cultural, Corporate and Commercial, Sports, Recreation + Entertainment, Education, Residential, Science + Technology, Transportation, Misc, Urban Design, Landscape Architecture, Government, Social Purpose, Health, Unknown / Other)
    - Delivery Type (select from: Construction Manager at Risk (CMaR), Design Only, Design-Bid-Build, Design-Build, Integrated Project Delivery (IPD), Guaranteed Maximum Price (GMP), Joint Venture (JV), Public Private Partnership (P3), Other)
    - Estimated Program Area
    - Estimated Budget
    - Sustainability Requirement
    - BIM Requirements

    Additional Information Aligned with Core Values:
    - Design Excellence Opportunities
    - Sustainability Initiatives
    - Resilience Measures
    - Innovation Potential
    - Diversity and Inclusion Aspects
    - Social Purpose Contributions
    - Well-Being Factors
    - Technological Innovation Opportunities
    
    If the information is not found, respond with 'Sorry, I could not find that information.'

    RFP Document Text:
    {extracted_text}
    """
    return pipeline_template
