import sys
import json
import logging
from typing import Any, Dict, Optional
from indexer import list_documents, get_document_content

# Configure logging to stderr so it doesn't interfere with stdout JSON-RPC
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MCPServer:
    def __init__(self):
        self.name = "founder-fire-kb"
        self.version = "0.1.0"

    def run(self):
        """Main loop to read from stdin and write to stdout."""
        logger.info("MCP Server starting...")
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                
                request = json.loads(line)
                response = self.handle_request(request)
                
                if response:
                    print(json.dumps(response), flush=True)
            except json.JSONDecodeError:
                logger.error("Invalid JSON received")
            except Exception as e:
                logger.error(f"Error in main loop: {e}")

    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        method = request.get("method")
        msg_id = request.get("id")
        params = request.get("params", {})

        logger.info(f"Received request: {method}")

        result = None
        error = None

        try:
            if method == "initialize":
                result = self.handle_initialize(params)
            elif method == "notifications/initialized":
                # No response needed for notifications
                return None
            elif method == "resources/list":
                result = self.handle_list_resources()
            elif method == "resources/read":
                result = self.handle_read_resource(params)
            elif method == "tools/list":
                result = self.handle_list_tools()
            elif method == "tools/call":
                result = self.handle_call_tool(params)
            elif method == "ping":
                result = {}
            else:
                error = {"code": -32601, "message": "Method not found"}
        except Exception as e:
            logger.error(f"Error handling {method}: {e}")
            error = {"code": -32000, "message": str(e)}

        response = {
            "jsonrpc": "2.0",
            "id": msg_id
        }
        if error:
            response["error"] = error
        else:
            response["result"] = result
        
        return response

    def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "protocolVersion": "2024-11-05",
            "serverInfo": {
                "name": self.name,
                "version": self.version
            },
            "capabilities": {
                "resources": {},
                "tools": {}
            }
        }

    def handle_list_resources(self) -> Dict[str, Any]:
        docs = list_documents()
        resources = []
        for doc in docs:
            resources.append({
                "uri": f"founder-fire://kb/{doc['filename']}",
                "name": doc['filename'],
                "mimeType": "text/plain",
                "description": f"{doc['type'].upper()} document, size: {doc['size']} bytes"
            })
        return {"resources": resources}

    def handle_read_resource(self, params: Dict[str, Any]) -> Dict[str, Any]:
        uri = params.get("uri")
        if not uri or not uri.startswith("founder-fire://kb/"):
            raise ValueError("Invalid URI")
        
        filename = uri.replace("founder-fire://kb/", "")
        content = get_document_content(filename)
        
        return {
            "contents": [{
                "uri": uri,
                "mimeType": "text/plain",
                "text": content
            }]
        }

    def handle_list_tools(self) -> Dict[str, Any]:
        return {
            "tools": [{
                "name": "search_knowledge_base",
                "description": "Search for keywords in the Founder FIRE knowledge base (PDFs/EPUBs).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query"
                        }
                    },
                    "required": ["query"]
                }
            }]
        }

    def handle_call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name")
        args = params.get("arguments", {})
        
        if name == "search_knowledge_base":
            query = args.get("query")
            if not query:
                return {"content": [{"type": "text", "text": "Error: Query is required."}]}

            results = []
            docs = list_documents()
            MAX_RESULTS = 5
            
            for doc in docs:
                try:
                    content = get_document_content(doc['filename'])
                    if query.lower() in content.lower():
                        # Find all occurrences
                        start_idx = 0
                        while True:
                            idx = content.lower().find(query.lower(), start_idx)
                            if idx == -1:
                                break
                            
                            # Extract snippet with context
                            start = max(0, idx - 100)
                            end = min(len(content), idx + 300)
                            snippet = content[start:end].replace("\n", " ")
                            results.append(f"Found in {doc['filename']}:\n...{snippet}...")
                            
                            if len(results) >= MAX_RESULTS:
                                break
                            
                            start_idx = idx + 1
                            
                    if len(results) >= MAX_RESULTS:
                        break
                except Exception as e:
                    logger.error(f"Error searching {doc['filename']}: {e}")
                    continue
            
            return {
                "content": [{
                    "type": "text",
                    "text": "\n\n".join(results) if results else "No matches found."
                }]
            }
        else:
            raise ValueError(f"Unknown tool: {name}")

if __name__ == "__main__":
    server = MCPServer()
    server.run()
