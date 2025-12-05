"""Summarizer service - generates intelligence summaries from scraped content."""

from typing import Dict, Optional, Callable
from dataclasses import dataclass


@dataclass
class SummaryConfig:
    """Configuration for summary generation."""
    max_content_chars: int = 50000
    include_sources: bool = True
    include_artifacts: bool = True
    include_recommendations: bool = True
    streaming: bool = True


class Summarizer:
    """
    Generates intelligence summaries from scraped dark web content.
    
    Uses LLM to analyze content and produce actionable threat intelligence.
    """
    
    SYSTEM_PROMPT = """
    You are a Cybercrime Threat Intelligence Expert tasked with generating context-based technical investigative insights from dark web OSINT search engine results.

    Rules:
    1. Analyze the Darkweb OSINT data provided using links and their raw text.
    2. Output the Source Links referenced for the analysis.
    3. Provide a detailed, contextual, evidence-based technical analysis of the data.
    4. Provide intelligence artifacts along with their context visible in the data.
    5. The artifacts can include indicators like name, email, phone, cryptocurrency addresses, domains, darkweb markets, forum names, threat actor information, malware names, TTPs, etc.
    6. Generate 3-5 key insights based on the data.
    7. Each insight should be specific, actionable, context-based, and data-driven.
    8. Include suggested next steps and queries for investigating more on the topic.
    9. Be objective and analytical in your assessment.
    10. Ignore not safe for work texts from the analysis.
    11. Structure your response with clear sections using Markdown formatting.

    Format your response as follows:
    
    ## Executive Summary
    [Brief overview of findings]
    
    ## Source Analysis
    [List of analyzed sources with key findings from each]
    
    ## Intelligence Artifacts
    [Extracted indicators organized by type]
    
    ## Key Insights
    [3-5 numbered insights]
    
    ## Threat Assessment
    [Risk level and context]
    
    ## Recommendations
    [Suggested next steps and follow-up queries]

    User Query: {query}

    Data to analyze:
    """
    
    def __init__(self, llm_provider, config: Optional[SummaryConfig] = None):
        """
        Initialize the summarizer.
        
        Args:
            llm_provider: LLM provider for summary generation
            config: Optional summary configuration
        """
        self.llm = llm_provider
        self.config = config or SummaryConfig()
    
    def summarize(
        self,
        query: str,
        scraped_content: Dict[str, str],
        stream_callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        Generate an intelligence summary from scraped content.
        
        Args:
            query: The original search query
            scraped_content: Dict mapping URLs to scraped text
            stream_callback: Optional callback for streaming output
            
        Returns:
            Generated intelligence summary
        """
        # Format content for LLM
        formatted_content = self._format_content(scraped_content)
        
        # Build prompt
        system_prompt = self.SYSTEM_PROMPT.format(query=query)
        
        # Generate summary
        if self.config.streaming and stream_callback:
            return self._summarize_streaming(
                system_prompt,
                formatted_content,
                stream_callback
            )
        else:
            return self._summarize_direct(system_prompt, formatted_content)
    
    def _summarize_direct(self, system_prompt: str, content: str) -> str:
        """Generate summary without streaming."""
        if hasattr(self.llm, 'get_langchain_llm'):
            return self._summarize_langchain(system_prompt, content)
        
        response = self.llm.complete(
            prompt=content,
            system_prompt=system_prompt
        )
        return response.content
    
    def _summarize_streaming(
        self,
        system_prompt: str,
        content: str,
        callback: Callable[[str], None]
    ) -> str:
        """Generate summary with streaming output."""
        if hasattr(self.llm, 'get_langchain_llm'):
            return self._summarize_langchain_streaming(
                system_prompt,
                content,
                callback
            )
        
        return self.llm.stream(
            prompt=content,
            system_prompt=system_prompt,
            callback=callback
        )
    
    def _summarize_langchain(self, system_prompt: str, content: str) -> str:
        """Generate summary using LangChain."""
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        
        llm = self.llm.get_langchain_llm()
        
        prompt_template = ChatPromptTemplate([
            ("system", system_prompt),
            ("user", "{content}")
        ])
        
        chain = prompt_template | llm | StrOutputParser()
        return chain.invoke({"content": content})
    
    def _summarize_langchain_streaming(
        self,
        system_prompt: str,
        content: str,
        callback: Callable[[str], None]
    ) -> str:
        """Generate summary using LangChain with streaming."""
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        
        llm = self.llm.get_langchain_llm()
        
        prompt_template = ChatPromptTemplate([
            ("system", system_prompt),
            ("user", "{content}")
        ])
        
        chain = prompt_template | llm | StrOutputParser()
        
        full_response = ""
        for chunk in chain.stream({"content": content}):
            full_response += chunk
            callback(chunk)
        
        return full_response
    
    def _format_content(self, scraped_content: Dict[str, str]) -> str:
        """Format scraped content for LLM processing."""
        lines = []
        total_chars = 0
        
        for url, text in scraped_content.items():
            # Check if we're approaching limit
            if total_chars >= self.config.max_content_chars:
                break
            
            # Clean and truncate text
            clean_text = ' '.join(text.split())
            remaining_chars = self.config.max_content_chars - total_chars
            
            if len(clean_text) > remaining_chars:
                clean_text = clean_text[:remaining_chars] + "..."
            
            lines.append(f"Source: {url}")
            lines.append(f"Content: {clean_text}")
            lines.append("")
            
            total_chars += len(clean_text) + len(url)
        
        return "\n".join(lines)
    
    async def asummarize(
        self,
        query: str,
        scraped_content: Dict[str, str]
    ) -> str:
        """Async version of summarize."""
        formatted_content = self._format_content(scraped_content)
        system_prompt = self.SYSTEM_PROMPT.format(query=query)
        
        response = await self.llm.acomplete(
            prompt=formatted_content,
            system_prompt=system_prompt
        )
        return response.content
