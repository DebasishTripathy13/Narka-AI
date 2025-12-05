"""Result filter service - uses LLM to filter relevant search results."""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class FilterConfig:
    """Configuration for result filtering."""
    max_results: int = 20
    truncate_title_length: int = 50
    truncate_link_length: int = 60
    min_relevance_score: float = 0.5


class ResultFilter:
    """
    Filters search results using LLM to identify most relevant matches.
    
    Takes raw search results and uses AI to select the most relevant
    ones for the given query.
    """
    
    SYSTEM_PROMPT = """
    You are a Cybercrime Threat Intelligence Expert. You are given a dark web search query and a list of search results in the form of index, link and title. 
    Your task is to select the Top {max_results} relevant results that best match the search query for user to investigate more.
    
    Rules:
    1. Output ONLY the indices (comma-separated list) that best match the input query
    2. Select at most {max_results} results
    3. Prioritize results that seem most relevant to the search query
    4. Consider both the title and domain when evaluating relevance
    5. Output only numbers separated by commas, nothing else

    Search Query: {query}
    Search Results:
    """
    
    def __init__(self, llm_provider, config: Optional[FilterConfig] = None):
        """
        Initialize the result filter.
        
        Args:
            llm_provider: LLM provider for filtering
            config: Optional filter configuration
        """
        self.llm = llm_provider
        self.config = config or FilterConfig()
    
    def filter(
        self,
        query: str,
        results: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """
        Filter search results to find most relevant matches.
        
        Args:
            query: The search query
            results: List of search results (dicts with 'title', 'link')
            
        Returns:
            Filtered list of most relevant results
        """
        if not results:
            return []
        
        # Format results for LLM
        formatted_results = self._format_results(results)
        
        # Build prompt
        system_prompt = self.SYSTEM_PROMPT.format(
            max_results=self.config.max_results,
            query=query
        )
        
        try:
            # Use LangChain if available
            if hasattr(self.llm, 'get_langchain_llm'):
                indices_str = self._filter_langchain(system_prompt, formatted_results)
            else:
                response = self.llm.complete(
                    prompt=formatted_results,
                    system_prompt=system_prompt
                )
                indices_str = response.content.strip()
            
            # Parse indices
            indices = self._parse_indices(indices_str, len(results))
            
            # Return filtered results
            return [results[i - 1] for i in indices if 0 < i <= len(results)]
            
        except Exception as e:
            # On error, return truncated results
            return results[:self.config.max_results]
    
    def _filter_langchain(self, system_prompt: str, formatted_results: str) -> str:
        """Filter using LangChain."""
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        
        llm = self.llm.get_langchain_llm()
        
        prompt_template = ChatPromptTemplate([
            ("system", system_prompt),
            ("user", "{results}")
        ])
        
        chain = prompt_template | llm | StrOutputParser()
        return chain.invoke({"results": formatted_results})
    
    def _format_results(
        self,
        results: List[Dict[str, str]],
        truncate: bool = False
    ) -> str:
        """Format results for LLM processing."""
        lines = []
        
        for i, res in enumerate(results, 1):
            link = res.get("link", "")
            title = res.get("title", "")
            
            # Clean title
            title = re.sub(r'[^0-9a-zA-Z\-\.\s]', ' ', title)
            title = ' '.join(title.split())  # Normalize whitespace
            
            # Truncate link to .onion domain
            truncated_link = re.sub(r'(?<=\.onion).*', '', link)
            
            if truncate:
                title = title[:self.config.truncate_title_length]
                truncated_link = truncated_link[:self.config.truncate_link_length]
            
            if truncated_link or title:
                lines.append(f"{i}. {truncated_link} - {title}")
        
        return "\n".join(lines)
    
    def _parse_indices(self, indices_str: str, max_index: int) -> List[int]:
        """Parse LLM output into list of indices."""
        indices = []
        
        # Extract all numbers from the response
        numbers = re.findall(r'\d+', indices_str)
        
        for num_str in numbers:
            try:
                num = int(num_str)
                if 1 <= num <= max_index and num not in indices:
                    indices.append(num)
                    if len(indices) >= self.config.max_results:
                        break
            except ValueError:
                continue
        
        return indices
    
    async def afilter(
        self,
        query: str,
        results: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Async version of filter."""
        if not results:
            return []
        
        formatted_results = self._format_results(results)
        
        system_prompt = self.SYSTEM_PROMPT.format(
            max_results=self.config.max_results,
            query=query
        )
        
        try:
            response = await self.llm.acomplete(
                prompt=formatted_results,
                system_prompt=system_prompt
            )
            
            indices = self._parse_indices(response.content, len(results))
            return [results[i - 1] for i in indices if 0 < i <= len(results)]
            
        except Exception:
            return results[:self.config.max_results]
