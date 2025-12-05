"""Query refiner service - uses LLM to optimize search queries."""

from typing import Optional
from dataclasses import dataclass


@dataclass
class RefinementConfig:
    """Configuration for query refinement."""
    max_query_length: int = 100
    add_context: bool = True
    remove_operators: bool = True


class QueryRefiner:
    """
    Refines user queries for dark web search engines using LLM.
    
    Transforms natural language queries into optimized search terms
    that yield better results from dark web search engines.
    """
    
    SYSTEM_PROMPT = """
    You are a Cybercrime Threat Intelligence Expert. Your task is to refine the provided user query that needs to be sent to darkweb search engines. 
    
    Rules:
    1. Analyze the user query and think about how it can be improved to use as search engine query
    2. Refine the user query by adding or removing words so that it returns the best result from dark web search engines
    3. Don't use any logical operators (AND, OR, etc.)
    4. Keep the query concise but specific
    5. Focus on terms that would appear in dark web content
    6. Output just the refined query and nothing else

    INPUT:
    """
    
    def __init__(self, llm_provider, config: Optional[RefinementConfig] = None):
        """
        Initialize the query refiner.
        
        Args:
            llm_provider: LLM provider for query refinement
            config: Optional refinement configuration
        """
        self.llm = llm_provider
        self.config = config or RefinementConfig()
    
    def refine(self, query: str) -> str:
        """
        Refine a search query using LLM.
        
        Args:
            query: The original user query
            
        Returns:
            Refined query optimized for dark web search
        """
        # Use LangChain if available
        if hasattr(self.llm, 'get_langchain_llm'):
            return self._refine_langchain(query)
        
        # Use direct LLM call
        response = self.llm.complete(
            prompt=query,
            system_prompt=self.SYSTEM_PROMPT
        )
        
        refined = response.content.strip()
        
        # Apply post-processing
        refined = self._post_process(refined)
        
        return refined
    
    def _refine_langchain(self, query: str) -> str:
        """Refine using LangChain."""
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        
        llm = self.llm.get_langchain_llm()
        
        prompt_template = ChatPromptTemplate([
            ("system", self.SYSTEM_PROMPT),
            ("user", "{query}")
        ])
        
        chain = prompt_template | llm | StrOutputParser()
        refined = chain.invoke({"query": query})
        
        return self._post_process(refined.strip())
    
    def _post_process(self, query: str) -> str:
        """Apply post-processing rules to refined query."""
        # Remove quotes if present
        query = query.strip('"\'')
        
        # Remove logical operators if configured
        if self.config.remove_operators:
            for op in ['AND', 'OR', 'NOT', '&&', '||']:
                query = query.replace(f' {op} ', ' ')
        
        # Truncate if too long
        if len(query) > self.config.max_query_length:
            query = query[:self.config.max_query_length].rsplit(' ', 1)[0]
        
        return query.strip()
    
    async def arefine(self, query: str) -> str:
        """Async version of refine."""
        response = await self.llm.acomplete(
            prompt=query,
            system_prompt=self.SYSTEM_PROMPT
        )
        
        refined = response.content.strip()
        return self._post_process(refined)
