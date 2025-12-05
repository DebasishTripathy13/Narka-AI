# Robin Architecture

## Overview

Robin follows a clean architecture pattern with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │     CLI     │  │   Web UI    │  │  REST API   │         │
│  │   (Click)   │  │ (Streamlit) │  │  (FastAPI)  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Core Layer                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    Services                          │   │
│  │  InvestigationService, EntityExtractor, Summarizer   │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    Entities                          │   │
│  │  Investigation, SearchResult, ScrapedContent, etc.   │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   Interfaces                         │   │
│  │  LLMProvider, SearchEngine, Storage, Cache, Export   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     Adapters Layer                           │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌─────────┐  │
│  │    LLM    │  │  Search   │  │  Storage  │  │ Export  │  │
│  │ Providers │  │  Engines  │  │  Backends │  │ Formats │  │
│  └───────────┘  └───────────┘  └───────────┘  └─────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                        │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐               │
│  │    Tor    │  │   Cache   │  │  Logging  │               │
│  │  Manager  │  │   Layer   │  │  System   │               │
│  └───────────┘  └───────────┘  └───────────┘               │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### Entities
Domain objects representing the core business concepts:
- `Investigation` - A complete OSINT investigation
- `SearchResult` - A single search result from a dark web engine
- `ScrapedContent` - Content extracted from a .onion page
- `ExtractedEntity` - Entities found in content (emails, wallets, etc.)

### Interfaces
Abstract base classes defining contracts for external integrations:
- `LLMProvider` - Interface for LLM providers
- `SearchEngineProvider` - Interface for search engines
- `StorageProvider` - Interface for data persistence
- `CacheProvider` - Interface for caching
- `ExportProvider` - Interface for export formats

### Services
Business logic implementation:
- `InvestigationService` - Orchestrates the investigation workflow
- `EntityExtractor` - Extracts entities from text using regex
- `ThreatAnalyzer` - Analyzes threat indicators
- `Summarizer` - Generates AI summaries

## Data Flow

```
User Input → CLI/UI/API
                │
                ▼
        InvestigationService
                │
    ┌───────────┼───────────┐
    ▼           ▼           ▼
 Search     Scrape      Analyze
    │           │           │
    ▼           ▼           ▼
 Results → Content → Entities
                │
                ▼
           AI Summary
                │
                ▼
             Export
```

## Plugin System

Robin supports plugins for extending functionality:
- Custom search engines
- Custom LLM providers
- Custom exporters
- Custom analyzers

See [Plugin Development](plugins.md) for details.
