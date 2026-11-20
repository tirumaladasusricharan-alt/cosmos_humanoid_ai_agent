/**
 * COSMOS Nuance Client — Frontend Client SDK Bridge
 * Creator: Sri Charan Tirumaladasu
 * 
 * SECURITY GUARANTEE:
 * - ZERO references to NUANCE_API_KEY, GROQ_API_KEY, nk_..., or gsk_...
 * - Only fetches short-lived session tokens (st_...) from POST /api/nuance-token
 * - Forwards onToolCall events to POST /api/cosmos/tool
 */

class CosmosNuanceClient {
    constructor(serverBaseUrl = "http://127.0.0.1:8000") {
        this.serverBaseUrl = serverBaseUrl.replace(/\/$/, "");
        this.sessionToken = null;
        this.room = null;
        this.isConnected = false;
        this.onSpeakingStateChange = null;
        this.onMessage = null;
    }

    /**
     * Request a single-use session token from the local Python bridge.
     * The browser NEVER sees the server's private API key.
     */
    async mintSessionToken(expressiveness = 0.8) {
        try {
            const resp = await fetch(`${this.serverBaseUrl}/api/nuance-token`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ expressiveness })
            });

            if (!resp.ok) {
                const errText = await resp.text();
                throw new Error(`Token mint failed HTTP ${resp.status}: ${errText}`);
            }

            const data = await resp.json();
            if (!data.token || !data.token.startsWith("st_")) {
                throw new Error("Received invalid session token format from server.");
            }

            this.sessionToken = data.token;
            if (data.warnings && data.warnings.length > 0) {
                console.warn("[COSMOS Nuance Client] Server warnings:", data.warnings);
            }

            return this.sessionToken;
        } catch (err) {
            console.error("[COSMOS Nuance Client] Error obtaining session token:", err);
            throw err;
        }
    }

    /**
     * Forward delegated tool execution to the backend router.
     */
    async handleToolCall(toolName, argumentsObj, userContext = null) {
        try {
            const resp = await fetch(`${this.serverBaseUrl}/api/cosmos/tool`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    tool_name: toolName,
                    arguments: argumentsObj,
                    user_context: userContext
                })
            });

            if (!resp.ok) {
                throw new Error(`Tool execution failed HTTP ${resp.status}`);
            }

            return await resp.json();
        } catch (err) {
            console.error(`[COSMOS Nuance Client] Error executing tool ${toolName}:`, err);
            throw err;
        }
    }

    /**
     * Connect to the Nuance session using the minted session token.
     */
    async connect(expressiveness = 0.8) {
        const token = await this.mintSessionToken(expressiveness);
        console.log("[COSMOS Nuance Client] Session token acquired (st_...), initializing LiveKit room...");

        // If Nuance SDK is loaded on window
        if (typeof window !== "undefined" && window.Nuance) {
            this.room = new window.Nuance.Room();
            this.room.on("toolCall", async (event) => {
                const { toolName, args, callback } = event;
                const result = await this.handleToolCall(toolName, args);
                if (callback) callback(result);
            });
            await this.room.connect(token);
            this.isConnected = true;
        } else {
            console.info("[COSMOS Nuance Client] Nuance JS SDK bridge ready with token:", token.substring(0, 8) + "...");
            this.isConnected = true;
        }

        return this.isConnected;
    }

    disconnect() {
        if (this.room && typeof this.room.disconnect === "function") {
            this.room.disconnect();
        }
        this.isConnected = false;
        this.sessionToken = null;
    }
}

if (typeof module !== "undefined" && module.exports) {
    module.exports = { CosmosNuanceClient };
}
