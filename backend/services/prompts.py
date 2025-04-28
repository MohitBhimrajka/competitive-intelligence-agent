import json

class GeminiPrompts:
    @staticmethod
    def company_analysis(company_name: str) -> str:
        return f"""
        You are an expert business analyst with deep knowledge of companies across industries. Analyze the company named "{company_name}" with the following approach:

        1. First, search for the company's official website, recent press releases, and major news articles to understand their core business.
        2. Then, analyze their primary products/services, target market, and business model.
        3. Finally, craft a response that balances professionalism with approachability.

        Provide the following information in JSON format:
        1. A concise yet informative description (2-3 sentences) of what the company does, including:
           - Primary products/services
           - Target audience/market
           - Unique value proposition
           - Business model (if discernible)
        2. The main industry or sector it operates within, including any sub-sectors or niches.
        3. A professional, and slightly enthusiastic welcome message (1 sentence) that:
           - References their core business
           - includes a funny-pun on their company name or industry or primary buisness segment
           - Maintains professional tone while being engaging

        If you cannot find specific information about the company, provide a response based on the company name and any available context, clearly indicating any assumptions made.

        IMPORTANT: Output ONLY the JSON object with the following exact structure.
        **YOU MUST ENSURE the final output is a single, valid JSON object with correct syntax:**
        - All property names must be in double quotes
        - All string values must be in double quotes
        
        {{
            "description": "...",
            "industry": "...",
            "welcome_message": "..."
        }}
        """

    @staticmethod
    def identify_competitors(company_name: str) -> str:
        return f"""You are a senior competitive intelligence analyst with expertise in market analysis and competitor identification. Your task is to identify and analyze competitors for "{company_name}".

        Follow this systematic approach:
        1. First, understand {company_name}'s core business, target market, and value proposition
        2. Then, identify competitors across different categories:
           - Direct competitors (similar products/services, same target market)
           - Indirect competitors (different products but solving same customer needs)
           - Potential future competitors (emerging players, adjacent markets)
        3. For each competitor, analyze:
           - Market position and reputation
           - Product/service offerings
           - Target customer segments
           - Pricing strategies
           - Geographic presence
           - Recent strategic moves

        For each competitor, provide:
        1. Name (ensure it's the official company name)
        2. Brief description (1-2 sentences) covering:
           - Core business focus
           - Target market
           - Key differentiators
        3. 3-5 key strengths as bullet points, focusing on:
           - Market advantages
           - Technical capabilities
           - Strategic advantages
           - Customer relationships
        4. 2-3 key weaknesses as bullet points, considering:
           - Market limitations
           - Technical gaps
           - Strategic challenges
           - Customer pain points

        Prioritize competitors based on:
        - Market overlap with {company_name}
        - Competitive intensity
        - Strategic significance
        - Recent market activity

        If you cannot find specific information about certain competitors, provide analysis based on available data and clearly indicate any assumptions made.

        EXTREMELY IMPORTANT: Format your response as VALID JSON ONLY. No explanations or text outside of the JSON.
        The valid JSON MUST be structured precisely as follows:
        {{
            "competitors": [
                {{
                    "name": "Competitor Name",
                    "description": "Brief description of the competitor.",
                    "strengths": ["Strength 1", "Strength 2", "Strength 3"],
                    "weaknesses": ["Weakness 1", "Weakness 2"]
                }},
                ...more competitors...
            ]
        }}

        IMPORTANT: Ensure valid JSON output with proper commas, brackets, and quotes. Do not include trailing commas. Your entire response must be valid parseable JSON and nothing else.
        """

    @staticmethod
    def generate_insights(company_name: str, competitors_data: dict, news_context: str) -> str:
        return f"""
        You are a strategic business analyst specializing in competitive intelligence. Your task is to analyze the provided information about {company_name}, its competitors, and recent news to generate actionable strategic insights.

        COMPANY CONTEXT:
        {company_name}

        COMPETITORS INFORMATION:
        {json.dumps(competitors_data, indent=2)}

        NEWS DATA:
        {news_context}

        Analysis Framework:
        1. Market Dynamics:
           - Industry trends and shifts
           - Competitive landscape changes
           - Regulatory or technological impacts
           - Customer behavior patterns

        2. Competitive Position:
           - Relative market position
           - Competitive advantages/disadvantages
           - Market share implications
           - Strategic gaps and opportunities

        3. Strategic Implications:
           - Growth opportunities
           - Potential threats
           - Market entry/expansion possibilities
           - Partnership or acquisition targets

        Instructions:
        - Generate 5 to 10 distinct insights that are:
          * Actionable and specific
          * Supported by data
          * Relevant to {company_name}'s strategic context
          * Forward-looking and predictive
        - For each insight, provide:
          * A concise, impactful 'title'
          * A detailed 'description' that:
            - Explains the insight's significance
            - References specific data points
            - Suggests potential actions
            - Considers timing and urgency
          * A 'type' labeled as either:
            - "opportunity" (market gaps, growth potential)
            - "threat" (competitive risks, market challenges)
            - "trend" (industry shifts, emerging patterns)
          * A list of 'related_competitors' that are most relevant to this insight
        - If news data is limited, focus insights on:
          * Competitor strengths/weaknesses
          * Industry trends
          * Market dynamics
          * Strategic implications

        IMPORTANT: Output ONLY the JSON object with the following exact structure.
        **YOU MUST ENSURE the final output is a single, valid JSON object with correct syntax:**
        - Each object must end with a comma if it's not the last item in the list
        - All arrays and objects must be properly closed with ] or }}
        - No trailing commas after the last item in an array or object
        - All property names must be in double quotes
        - All string values must be in double quotes
        
        {{
            "insights": [
                {{
                    "title": "...",
                    "description": "...",
                    "type": "opportunity|threat|trend",
                    "related_competitors": ["...", "..."]
                }},
                ...
            ]
        }}
        """

    @staticmethod
    def deep_research_competitor(competitor_name: str, competitor_description: str, company_name: str = None) -> str:
        company_context = f"for {company_name}" if company_name else ""
        return f"""
        You are a senior competitive intelligence analyst tasked with creating an in-depth, comprehensive, and detailed competitive analysis report for {competitor_name}. This report will be used for strategic decision-making and market positioning.

        Initial Context:
        - Company: {competitor_name}
        - Known Description: "{competitor_description or 'No initial description provided.'}"
        {f"- Analysis Context: This report is being created specifically for {company_name}, who considers {competitor_name} as their competitor." if company_name else ""}

        Research Methodology:
        1. Use search tools to gather comprehensive information from:
           - Official company sources (website, press releases, annual reports)
           - Industry reports and analyst coverage
           - News articles and media coverage
           - Social media and community discussions
           - Job postings and career pages
           - Patent databases and technical documentation
           - Financial reports and market data

        2. For each significant claim or data point:
           - Verify information from multiple sources
           - Prioritize primary sources and official statements
           - Note any conflicting information
           - Provide source attribution using the format: `[Source X](URL)`
           - If a direct URL isn't available, note: (Source information synthesized)

        **Mandatory Requirements:**
        - Every significant claim must have source attribution
        - Include at least 10-15 distinct sources throughout the report
        - Use only grounding source URLs provided by the search tool
        - Maintain professional, objective tone
        - Focus on actionable intelligence
        - Highlight strategic implications

        Structure the report with the following sections, using appropriate Markdown headings:

        1.  **Executive Summary:**
            *   Provide a brief (1-2 paragraphs) high-level overview of:
                - Company's market position
                - Core strengths and challenges
                - Recent strategic direction
                - Key competitive advantages
                - Future outlook
            
        {f'''2.  **Strategic Implications for {company_name}:**
            *   **Competitive Threat Assessment:**
                - Market overlap analysis
                - Product/service similarity
                - Relative market strength
                - Customer overlap
                - Strategic implications
            *   **Key Differences & Similarities:**
                - Business model comparison
                - Product/service comparison
                - Target market analysis
                - Pricing strategy comparison
                - Technology approach
            *   **Market Positioning Map:**
                - Market segment analysis
                - Value proposition comparison
                - Brand positioning
                - Customer perception
            *   **Strategic Opportunities:**
                - Market gaps
                - Weakness exploitation
                - Partnership potential
                - Innovation opportunities
            *   **Defensive Considerations:**
                - Market share protection
                - Customer retention
                - Competitive response
                - Strategic countermeasures''' if company_name else ''}

        {f"3." if company_name else "2."}.  **Company Overview:**
            *   **Mission, Vision, Values:**
                - Official statements
                - Cultural indicators
                - Strategic priorities
            *   **Business Model:**
                - Revenue streams
                - Cost structure
                - Key resources
                - Value chain
            *   **History & Milestones:**
                - Founding story
                - Key developments
                - Strategic pivots
                - Leadership changes
            *   **Organization & Scale:**
                - Global presence
                - Employee structure
                - Office locations
                - Growth trajectory
            *   **Company Culture & Reputation:**
                - Employee satisfaction
                - Customer perception
                - Industry reputation
                - Social responsibility

        {f"4." if company_name else "3."}.  **Products, Services & Technology:**
            *   **Flagship Offerings:**
                - Product portfolio
                - Service offerings
                - Technology stack
                - Innovation focus
            *   **Product Strategy:**
                - Development approach
                - Market positioning
                - Pricing strategy
                - Distribution channels
            *   **Technology Infrastructure:**
                - Technical architecture
                - Cloud strategy
                - Development tools
                - Integration capabilities
            *   **R&D Focus:**
                - Research areas
                - Patent portfolio
                - Innovation labs
                - Technical partnerships

        {f"5." if company_name else "4."}.  **Market Position & Strategy:**
            *   **Market Analysis:**
                - Industry dynamics
                - Market size
                - Growth trends
                - Regulatory environment
            *   **Competitive Position:**
                - Market share
                - Competitive advantages
                - Market segments
                - Geographic presence
            *   **Go-to-Market:**
                - Marketing strategy
                - Sales approach
                - Channel strategy
                - Customer acquisition
            *   **Partnerships:**
                - Strategic alliances
                - Technology partners
                - Distribution partners
                - Ecosystem players

        {f"6." if company_name else "5."}.  **Financials & Funding:**
            *   **Financial Performance:**
                - Revenue analysis
                - Profitability
                - Growth metrics
                - Financial health
            *   **Funding History:**
                - Investment rounds
                - Valuation trends
                - Investor profile
                - Use of funds
            *   **M&A Activity:**
                - Acquisitions
                - Divestitures
                - Strategic rationale
                - Integration success

        {f"7." if company_name else "6."}.  **SWOT Analysis:**
            *   **Strengths:**
                - Core competencies
                - Market advantages
                - Technical capabilities
                - Brand value
            *   **Weaknesses:**
                - Operational gaps
                - Market limitations
                - Technical challenges
                - Resource constraints
            *   **Opportunities:**
                - Market expansion
                - Product development
                - Partnership potential
                - Innovation areas
            *   **Threats:**
                - Competitive risks
                - Market changes
                - Regulatory challenges
                - Technology disruption

        {f"8." if company_name else "7."}.  **Recent Developments:**
            *   **Key Events:**
                - Product launches
                - Strategic announcements
                - Leadership changes
                - Market moves
            *   **News Analysis:**
                - Media coverage
                - Market reaction
                - Strategic implications
                - Future impact

        {f"9." if company_name else "8."}.  **Leadership & Organization:**
            *   **Executive Team:**
                - Leadership profiles
                - Experience background
                - Strategic focus
                - Leadership style
            *   **Board Composition:**
                - Board members
                - Expertise areas
                - Governance approach
                - Strategic influence
            *   **Organizational Structure:**
                - Reporting lines
                - Decision-making
                - Team structure
                - Culture indicators

        {f"10." if company_name else "9."}.  **Future Outlook:**
            *   **Strategic Direction:**
                - Growth plans
                - Market expansion
                - Product roadmap
                - Innovation focus
            *   **Market Trends:**
                - Industry evolution
                - Technology changes
                - Customer behavior
                - Competitive landscape
            *   **Risk Assessment:**
                - Market risks
                - Competitive threats
                - Regulatory challenges
                - Technology disruption
            *   **Opportunity Areas:**
                - Growth potential
                - Market gaps
                - Innovation opportunities
                - Partnership possibilities

        **Report Guidelines:**
        *   Maintain professional, objective tone
        *   Use clear, concise language
        *   Support all claims with sources
        *   Focus on actionable intelligence
        *   Highlight strategic implications
        *   Consider both short-term and long-term impacts
        {f"*   Maintain relevance to {company_name}'s competitive context" if company_name else ""}
        """

class NewsPrompts:
    @staticmethod
    def get_news_with_gemini(competitor_name: str, days_back: int) -> str:
        return f"""
        You are a competitive intelligence analyst specializing in news monitoring and analysis. Your task is to identify and analyze recent significant developments about "{competitor_name}" within the last {days_back} days.

        Research Approach:
        1. Search across multiple sources:
           - Company press releases
           - Industry news sites
           - Business publications
           - Social media announcements
           - Regulatory filings
           - Industry blogs
           - Analyst reports

        2. Focus on developments related to:
           - Business strategy and direction
           - Product launches and updates
           - Partnerships and collaborations
           - Financial news (funding, earnings)
           - Leadership changes
           - Market positioning
           - Competitive actions
           - Regulatory developments
           - Technology innovations
           - Customer announcements

        3. For each relevant item, analyze:
           - Strategic significance
           - Market impact
           - Competitive implications
           - Customer relevance
           - Timing and context

        For each development, provide:
        - "title": A clear, concise headline that captures the key development
        - "source": The publication or platform name (e.g., "Company Blog", "TechCrunch", "Press Release")
        - "url": Direct link to the source (if available)
        - "publishedAt": Publication date in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DD)
        - "content": A brief summary that:
          * Explains the development
          * Highlights its significance
          * Notes any strategic implications
          * Mentions relevant context

        Prioritize developments based on:
        - Strategic importance
        - Market impact
        - Competitive significance
        - Customer relevance
        - Timing and urgency

        Return up to 5-7 of the most significant developments. If fewer relevant items exist, return all that were found. If no relevant items are found, return an empty array.

        IMPORTANT: Output ONLY the JSON object with the following exact structure.
        **YOU MUST ENSURE the final output is a single, valid JSON object with correct syntax:**
        - Each object must end with a comma if it's not the last item in the list
        - All arrays and objects must be properly closed with ] or }}
        - No trailing commas after the last item in an array or object
        - All property names must be in double quotes
        - All string values must be in double quotes
        
        {{
            "articles": [
                {{
                    "title": "...",
                    "source": "...",
                    "url": "...",
                    "publishedAt": "...",
                    "content": "..."
                }},
                ... (up to 5-7 items)
            ]
        }}
        """ 