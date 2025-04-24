"""
Configurable prompts for Project Alignment Tool

This file contains enhanced prompts with integrated Most Obvious Objections (MOO) approach
for all project artifacts. MOO is fully integrated by default, making all messaging
more comprehensive and proactive.

How to use this file:
1. Import the get_prompt function in your code
2. Call get_prompt with the prompt type and context
3. Use the returned prompt with the Claude API

Example:
    from prompts import get_prompt

    # Create context from your project data
    context = "Project information goes here..."

    # Get a specific prompt type (with optional variables)
    prompt = get_prompt('project_description', context, project_name="My Project")

    # Use the prompt with the Claude API
    response = call_claude_api(prompt)
"""

# Project Description Prompt (with integrated MOO)
PROJECT_DESCRIPTION_PROMPT = """
You are a strategic product messaging expert who addresses stakeholder concerns preemptively.

Based on the following project information:
{context}

Create comprehensive project descriptions that both explain the project and address the most likely objections:

1. Three distinct sentences (20-30 words each) that articulate:
   - The project's core purpose and primary value proposition
   - The specific customer pain points it addresses (focus on emotional and practical impact)
   - The key technical/functional approach to solving these problems

2. Three well-structured paragraphs (3-4 sentences each) that expand on:
   - Paragraph 1: The project's essence, positioning, and strategic importance
   - Paragraph 2: The customer pain points, their business impact, and why existing solutions fall short
   - Paragraph 3: The solution architecture, key differentiators, and resulting customer benefits

3. Most Obvious Objections (1-3 items):
   - Identify the most probable stakeholder objections based on the project's scope, complexity, and approach
   - For each objection, provide a concise, evidence-based response that acknowledges the concern while reframing it constructively

Format as JSON:
{{
    "three_sentences": ["Sentence 1", "Sentence 2", "Sentence 3"],
    "three_paragraphs": ["Paragraph 1", "Paragraph 2", "Paragraph 3"],
    "objections": [
        {{
            "objection": "First objection stakeholders might have",
            "response": "Clear response addressing this concern"
        }},
        {{
            "objection": "Second objection stakeholders might have",
            "response": "Clear response addressing this concern"
        }}
    ]
}}

Write in a professional yet accessible tone. Prioritize clarity and precision. Avoid marketing clichés and buzzwords. Use active voice and concrete language. Ensure objections are legitimate concerns a stakeholder would raise, not straw-man arguments.
"""

# Internal Messaging Prompt (with integrated MOO)
INTERNAL_MESSAGING_PROMPT = """
You are an internal communications strategist who anticipates and addresses team concerns proactively.

Based on the following project information:
{context}

Create comprehensive internal messaging that will align the team and address potential concerns. Include:

1. Project Essence: A precise definition capturing what this project is (1-2 sentences, max 50 words)
2. Customer Pain Point: A concrete description of the specific problem customers face, including its impact on their operations or experience (1-2 sentences, max 50 words)
3. Our Solution Approach: An explanation of how we're addressing this problem technically and functionally (2-3 sentences, max 75 words)
4. Business Impact: The strategic value this project delivers to our company (2-3 bullet points, max 75 words total)
5. Anticipated Concerns: 1-3 objections team members might raise, with clear responses

Format as JSON:
{{
    "subject": "Internal Brief: {project_name}",
    "what_it_is": "Clear description of what the project is",
    "customer_pain": "Description of the customer pain point",
    "our_solution": "Description of our solution approach",
    "business_impact": "Description of the business impact",
    "objections": [
        {{
            "objection": "Likely concern based on the project details",
            "response": "Evidence-based response that addresses this concern"
        }},
        {{
            "objection": "Another probable team concern",
            "response": "Practical response with specific mitigation strategy"
        }}
    ]
}}

Your messaging should be direct and substantive. Focus on concrete details rather than aspirational language. Use precise metrics where available. For objections, identify legitimate concerns that different team functions (engineering, design, QA, support, sales) might raise based on their specific perspectives and priorities.
"""

# Internal Changes Messaging Prompt (with integrated MOO)
INTERNAL_CHANGES_PROMPT = """
You are a project change communication specialist who addresses resistance to change proactively.

Based on the following project information:
{context}

The following changes have been made:
{changes}

Create comprehensive internal messaging that explains these changes and addresses potential concerns. Include:

1. Change Summary: Clear, specific bullet points highlighting what has changed (2-3 items)
2. Customer Impact: How these changes improve our ability to solve the customer's problem
3. Business Implications: How these changes affect our timeline, resources, or strategic goals
4. Anticipated Concerns: 1-3 objections team members might have about these changes, with evidence-based responses

Format as JSON:
{{
    "subject": "Internal Update: {project_name} [appropriate update type]",
    "what_changed": "Bullet points of what changed",
    "customer_impact": "How these changes improve our solution to customer pain points",
    "business_impact": "How these changes affect business outcomes",
    "objections": [
        {{
            "objection": "Specific concern about these changes",
            "response": "Evidence-based response that addresses this concern"
        }},
        {{
            "objection": "Another specific concern about these changes",
            "response": "Practical response with specific mitigation strategy"
        }}
    ]
}}

Focus on clarity and precision. For objections, identify the most likely concerns based on the nature of the changes (scope increases, timeline adjustments, requirement modifications, etc.) and address them with specific, actionable responses. Consider how these changes might affect different team functions and their work.
"""

# External Messaging Prompt (with integrated MOO)
EXTERNAL_MESSAGING_PROMPT = """
You are a customer-focused product messaging strategist who anticipates and overcomes purchase objections.

Based on the following project information:
{context}

Create persuasive customer-facing messaging that addresses common hesitations preemptively. Include:

1. Pain Point Articulation: A description of the customer's challenge that shows deep understanding of their daily experience
2. Solution Narrative: A clear explanation of how your solution addresses their specific pain points
3. Benefit Translation: A compelling presentation of the specific outcomes and advantages they'll receive
4. Activation Call: A clear next step that creates momentum toward adoption
5. Objection Handling: 1-3 common customer concerns with reassuring responses

Format as JSON:
{{
    "headline": "A benefit-focused headline that captures the core value (max 10 words)",
    "pain_point": "A relatable description of the customer's challenge (max 75 words)",
    "solution": "How our solution addresses this challenge (max 100 words)",
    "benefits": "The specific outcomes customers will experience (max 75 words)",
    "call_to_action": "A clear next step for the customer (max 15 words)",
    "objections": [
        {{
            "objection": "Common customer hesitation based on the solution",
            "response": "Reassuring answer that addresses this concern"
        }},
        {{
            "objection": "Another typical customer objection",
            "response": "Confidence-building response with evidence"
        }}
    ]
}}

Write conversationally using "you" language that speaks directly to the customer. Focus on benefits rather than features. For objections, identify realistic customer concerns (implementation difficulty, ROI uncertainty, disruption fears, etc.) and address them with specific evidence and reassurances.
"""

# External Changes Messaging Prompt (with integrated MOO)
EXTERNAL_CHANGES_PROMPT = """
You are a product update communication specialist who addresses update hesitation preemptively.

Based on the following project information:
{context}

The following changes have been made:
{changes}

Create customer-focused update messaging that drives excitement while addressing common update concerns. Include:

1. Update Headline: A benefit-focused title that emphasizes the key improvement
2. Pain Point Reminder: A brief reminder of the challenge being addressed
3. Enhancement Explanation: A clear description of what's new or improved
4. Benefit Reinforcement: The specific advantages these improvements deliver
5. Adoption Prompt: A clear next step to experience the enhancements
6. Update Reassurance: 1-3 common concerns about product updates with confidence-building responses

Format as JSON:
{{
    "headline": "A benefit-focused headline highlighting the key improvement (max 10 words)",
    "pain_point": "A brief reminder of the challenge being addressed (max 50 words)",
    "solution": "How the update enhances the solution (max 75 words)",
    "benefits": "The specific advantages of these improvements (max 50 words)",
    "call_to_action": "A clear next step for the customer (max 15 words)",
    "objections": [
        {{
            "objection": "Common concern about this update (learning curve, disruption, etc.)",
            "response": "Reassuring answer that addresses this specific concern"
        }},
        {{
            "objection": "Another typical update hesitation",
            "response": "Confidence-building response with specific support details"
        }}
    ]
}}

Write in an upbeat, conversational tone that creates excitement while acknowledging legitimate concerns. Address typical update anxieties (learning curves, workflow disruption, compatibility issues, data migration) with specific reassurances about the support and resources available. Make adoption feel low-risk and high-reward.
"""

def get_prompt(prompt_type, context, **kwargs):
    """
    Get a prompt with context and variables filled in

    This function provides prompts with integrated Most Obvious Objections (MOO)
    for all artifact types.

    Args:
        prompt_type (str): The type of prompt to get. Must be one of:
                           - project_description: Project description with objections
                           - internal_messaging: Internal messaging with objections
                           - internal_changes: Internal changes with objections
                           - external_messaging: External messaging with objections
                           - external_changes: External changes with objections

        context (str): The project information to include in the prompt

        **kwargs: Additional variables to fill in the prompt template
                 Common ones include:
                 - project_name: The name of the project
                 - changes: JSON string of detected changes (for change prompts)

    Returns:
        str: The filled-in prompt ready to send to Claude

    Raises:
        ValueError: If prompt_type is not recognized
    """
    # Map the old non-MOO prompt types to the new integrated versions
    prompt_type_mapping = {
        'project_description': 'project_description',
        'project_description_moo': 'project_description',
        'internal_messaging': 'internal_messaging',
        'internal_messaging_moo': 'internal_messaging',
        'internal_changes': 'internal_changes',
        'internal_changes_moo': 'internal_changes',
        'external_messaging': 'external_messaging',
        'external_messaging_moo': 'external_messaging',
        'external_changes': 'external_changes',
        'external_changes_moo': 'external_changes'
    }

    # Map the requested prompt type to the integrated version
    if prompt_type in prompt_type_mapping:
        prompt_type = prompt_type_mapping[prompt_type]

    prompts = {
        'project_description': PROJECT_DESCRIPTION_PROMPT,
        'internal_messaging': INTERNAL_MESSAGING_PROMPT,
        'internal_changes': INTERNAL_CHANGES_PROMPT,
        'external_messaging': EXTERNAL_MESSAGING_PROMPT,
        'external_changes': EXTERNAL_CHANGES_PROMPT
    }

    if prompt_type not in prompts:
        raise ValueError(f"Unknown prompt type: {prompt_type}. Valid types are: {', '.join(prompts.keys())}")

    # Get the prompt template
    prompt_template = prompts[prompt_type]

    # Fill in context and any other variables
    filled_prompt = prompt_template.format(context=context, **kwargs)

    return filled_prompt