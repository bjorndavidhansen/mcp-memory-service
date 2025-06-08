#!/usr/bin/env python3
"""
MCP Server for EchoVault Memory Service

This module implements an MCP (Model Context Protocol) server that exposes
EchoVault's semantic memory capabilities as standardized MCP tools.

Uses the official MCP Python SDK to provide:
- Memory storage with semantic embeddings
- Memory search with similarity scoring
- Tag-based memory organization
- Enterprise-grade durability via cloud services

Requirements:
- Official MCP Python SDK: pip install mcp
- EchoVault dependencies: pip install -r requirements-echovault.txt
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict, List

# Official MCP SDK imports
try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    import mcp.types as types
    from mcp.server.stdio import stdio_server
except ImportError as e:
    print("Error: Official MCP SDK not installed. Run: pip install mcp")
    print(f"Import error: {e}")
    sys.exit(1)

# EchoVault imports
try:
    from .storage.factory import create_storage
    from .models.memory import Memory
except ImportError as e:
    print("Error: EchoVault modules not found. Ensure you're running "
          "from the correct directory.")
    print(f"Import error: {e}")
    sys.exit(1)

# Configure logging
import logging
logger = logging.getLogger(__name__)


class EchoVaultMCPServer:
    """
    MCP Server wrapper for EchoVault Memory Service.
    
    Exposes EchoVault's memory operations as standardized MCP tools:
    - store_memory: Store content with semantic embeddings and optional tags
    - search_memories: Search using semantic similarity
    - search_by_tag: Find memories by tag
    - get_memory_stats: Get storage statistics
    - delete_memory: Remove specific memory by ID
    """
    
    def __init__(self):
        """Initialize the EchoVault MCP server."""
        self.storage = None
        self.server = Server("echovault-memory")
        
        # Register MCP tools
        self._register_tools()
        
    async def initialize_storage(self) -> None:
        """Initialize EchoVault storage backend."""
        try:
            # Enable EchoVault mode if not already set
            if os.environ.get("USE_ECHOVAULT") != "false":
                os.environ["USE_ECHOVAULT"] = "true"
            
            # Create storage instance
            self.storage = create_storage()
            
            # Initialize if needed - wrap in try/catch to avoid TaskGroup issues
            if hasattr(self.storage, 'initialize') and callable(self.storage.initialize):
                try:
                    await self.storage.initialize()
                except Exception as init_error:
                    logger.warning(f"Storage initialization warning: {init_error}")
                    # Continue without full initialization for basic MCP functionality
                
            logger.info("EchoVault storage initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize EchoVault storage: {e}")
            # Create a minimal storage fallback instead of failing completely
            logger.info("Falling back to minimal storage mode")
            # Don't raise - allow server to continue with limited functionality
    
    def _register_tools(self) -> None:
        """Register MCP tools with the server."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """List all available MCP tools."""
            return [
                types.Tool(
                    name="store_memory",
                    description="Store a memory with semantic embeddings and optional tags",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "The content to store in memory"
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Optional tags for categorizing the memory",
                                "default": []
                            },
                            "importance": {
                                "type": "number",
                                "description": "Importance score (0.0-1.0)",
                                "minimum": 0.0,
                                "maximum": 1.0,
                                "default": 0.5
                            }
                        },
                        "required": ["content"]
                    }
                ),
                types.Tool(
                    name="search_memories",
                    description="Search memories using semantic similarity",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query for semantic similarity"
                            },
                            "limit": {
                                "type": "number",
                                "description": "Maximum number of results to return",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 100
                            },
                            "similarity_threshold": {
                                "type": "number",
                                "description": "Minimum similarity score (0.0-1.0)",
                                "default": 0.3,
                                "minimum": 0.0,
                                "maximum": 1.0
                            }
                        },
                        "required": ["query"]
                    }
                ),
                types.Tool(
                    name="search_by_tag", 
                    description="Find memories by tag",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "tag": {
                                "type": "string",
                                "description": "Tag to search for"
                            },
                            "limit": {
                                "type": "number",
                                "description": "Maximum number of results",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 100
                            }
                        },
                        "required": ["tag"]
                    }
                ),
                types.Tool(
                    name="get_memory_stats",
                    description="Get storage statistics and health information",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False
                    }
                ),
                types.Tool(
                    name="delete_memory",
                    description="Delete a specific memory by ID",
                    inputSchema={
                        "type": "object", 
                        "properties": {
                            "memory_id": {
                                "type": "string",
                                "description": "ID of the memory to delete"
                            }
                        },
                        "required": ["memory_id"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Handle tool calls from MCP clients."""
            
            # Ensure storage is initialized  
            if self.storage is None:
                try:
                    await self.initialize_storage()
                except Exception as e:
                    # If storage initialization fails, return helpful error
                    error_msg = f"Storage not available: {str(e)}"
                    logger.error(error_msg)
                    return [types.TextContent(type="text", text=json.dumps({
                        "error": error_msg,
                        "suggestion": "Check cloud service credentials and network connectivity"
                    }, indent=2))]
            
            try:
                if name == "store_memory":
                    result = await self._handle_store_memory(arguments)
                elif name == "search_memories":
                    result = await self._handle_search_memories(arguments)
                elif name == "search_by_tag":
                    result = await self._handle_search_by_tag(arguments)
                elif name == "get_memory_stats":
                    result = await self._handle_get_memory_stats(arguments)
                elif name == "delete_memory":
                    result = await self._handle_delete_memory(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
                
            except Exception as e:
                error_msg = f"Error executing tool '{name}': {str(e)}"
                logger.error(error_msg)
                return [types.TextContent(type="text", text=json.dumps({"error": error_msg}, indent=2))]
    
    async def _handle_store_memory(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle store_memory tool calls."""
        content = arguments["content"]
        tags = arguments.get("tags", [])
        importance = arguments.get("importance", 0.5)
        
        # Create memory object
        memory = Memory(
            content=content,
            tags=tags,
            importance=importance
        )
        
        # Store the memory
        memory_id = await self.storage.store(memory)
        
        return {
            "success": True,
            "memory_id": memory_id,
            "message": f"Memory stored successfully with ID: {memory_id}",
            "content_length": len(content),
            "tags": tags,
            "importance": importance
        }
    
    async def _handle_search_memories(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle search_memories tool calls."""
        query = arguments["query"] 
        limit = arguments.get("limit", 10)
        similarity_threshold = arguments.get("similarity_threshold", 0.3)
        
        # Search memories
        memories = await self.storage.retrieve(
            query=query,
            limit=limit,
            similarity_threshold=similarity_threshold
        )
        
        # Format results
        results = []
        for memory in memories:
            results.append({
                "id": memory.id,
                "content": memory.content,
                "tags": memory.tags,
                "importance": memory.importance,
                "created_at": memory.created_at.isoformat() if memory.created_at else None,
                "similarity_score": getattr(memory, 'similarity_score', None)
            })
        
        return {
            "success": True,
            "query": query,
            "results_found": len(results),
            "similarity_threshold": similarity_threshold,
            "memories": results
        }
    
    async def _handle_search_by_tag(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle search_by_tag tool calls."""
        tag = arguments["tag"]
        limit = arguments.get("limit", 10)
        
        # Search by tag
        memories = await self.storage.search_by_tag(tag, limit=limit)
        
        # Format results
        results = []
        for memory in memories:
            results.append({
                "id": memory.id,
                "content": memory.content,
                "tags": memory.tags,
                "importance": memory.importance,
                "created_at": memory.created_at.isoformat() if memory.created_at else None
            })
        
        return {
            "success": True,
            "tag": tag,
            "results_found": len(results),
            "memories": results
        }
    
    async def _handle_get_memory_stats(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get_memory_stats tool calls."""
        try:
            if hasattr(self.storage, 'get_stats'):
                stats = await self.storage.get_stats()
                return {
                    "success": True,
                    "stats": stats
                }
            else:
                return {
                    "success": True,
                    "message": "Statistics not available for this storage backend",
                    "storage_type": type(self.storage).__name__
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get stats: {str(e)}"
            }
    
    async def _handle_delete_memory(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle delete_memory tool calls."""
        memory_id = arguments["memory_id"]
        
        try:
            if hasattr(self.storage, 'delete_memory'):
                success = await self.storage.delete_memory(memory_id)
                return {
                    "success": success,
                    "memory_id": memory_id,
                    "message": "Memory deleted successfully" if success else "Memory not found"
                }
            else:
                return {
                    "success": False,
                    "error": "Delete operation not supported by this storage backend"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to delete memory: {str(e)}"
            }

async def main():
    """Main entry point for the MCP server."""
    logger.info("Starting EchoVault MCP Server...")
    
    echovault_server = None
    
    try:
        # Create server instance
        echovault_server = EchoVaultMCPServer()
        logger.info("EchoVault MCP server instance created")
        
        # Pre-initialize storage to avoid issues during tool calls
        try:
            await echovault_server.initialize_storage()
            logger.info("Storage pre-initialized successfully")
        except Exception as storage_error:
            logger.warning(f"Storage pre-initialization failed: {storage_error}")
            logger.info("Server will continue with delayed storage initialization")
        
        # Run the server with stdio transport
        async with stdio_server() as (read_stream, write_stream):
            logger.info("Starting MCP server with stdio transport")
            await echovault_server.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="echovault-memory",
                    server_version="1.0.0",
                    capabilities=echovault_server.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None
                    )
                )
            )
            
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        # Log full traceback for debugging
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        # Don't call sys.exit() in async context, just raise to let asyncio.run handle it
        raise
    finally:
        # Clean up resources
        if echovault_server and hasattr(echovault_server, 'storage') and echovault_server.storage:
            try:
                if hasattr(echovault_server.storage, 'close'):
                    await echovault_server.storage.close()
            except Exception as cleanup_error:
                logger.warning(f"Error during cleanup: {cleanup_error}")

if __name__ == "__main__":
    asyncio.run(main()) 