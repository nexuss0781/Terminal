<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Interactive web terminal with real-time communication">
    <meta name="theme-color" content="#282a36">
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>💻</text></svg>">
    <title>Web Terminal • Modern Interface</title>
    
    <!-- Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@300;400;500;700&display=swap" rel="stylesheet">
    
    <!-- Xterm.js -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm@5.3.0/css/xterm.min.css" />
    
    <style>
        :root {
            /* Dracula Theme Colors */
            --bg-primary: #282a36;
            --bg-secondary: #44475a;
            --fg-primary: #f8f8f2;
            --fg-secondary: #6272a4;
            --cursor-color: #f8f8f0;
            --selection-bg: rgba(68, 71, 90, 0.8);
            --status-online: #50fa7b;
            --status-offline: #ff5555;
            --status-connecting: #ffb86c;
            --border-radius: 8px;
            --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.2);
            --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.3);
            --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            display: flex;
            flex-direction: column;
            min-height: 100vh;
            background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3a 100%);
            color: var(--fg-primary);
            font-family: 'Fira Code', monospace;
            overflow: hidden;
            padding: 1rem;
        }

        .terminal-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.5rem 1rem;
            background: rgba(40, 42, 54, 0.9);
            border-radius: var(--border-radius) var(--border-radius) 0 0;
            box-shadow: var(--shadow-sm);
            backdrop-filter: blur(4px);
            z-index: 10;
            border-bottom: 1px solid var(--bg-secondary);
        }

        .terminal-title {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-weight: 500;
            font-size: 1.1rem;
        }

        .terminal-title svg {
            width: 1.2rem;
            height: 1.2rem;
            color: var(--status-online);
        }

        .connection-status {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.85rem;
            color: var(--fg-secondary);
        }

        .status-indicator {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--status-offline);
            transition: var(--transition);
        }

        .status-indicator.online {
            background: var(--status-online);
            box-shadow: 0 0 6px var(--status-online);
        }

        .status-indicator.connecting {
            background: var(--status-connecting);
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(255, 184, 108, 0.7); }
            70% { box-shadow: 0 0 0 6px rgba(255, 184, 108, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 184, 108, 0); }
        }

        #terminal-container {
            flex: 1;
            min-height: 0;
            border-radius: 0 0 var(--border-radius) var(--border-radius);
            overflow: hidden;
            box-shadow: var(--shadow-md);
            position: relative;
            background: var(--bg-primary);
            margin-top: 0.25rem;
        }

        .terminal-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(40, 42, 54, 0.95);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 20;
            transition: opacity 0.3s ease;
        }

        .terminal-overlay.hidden {
            opacity: 0;
            pointer-events: none;
        }

        .overlay-content {
            text-align: center;
            padding: 2rem;
            max-width: 80%;
        }

        .overlay-title {
            font-size: 1.8rem;
            margin-bottom: 1rem;
            background: linear-gradient(45deg, var(--status-online), var(--status-connecting));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700;
        }

        .overlay-message {
            font-size: 1.1rem;
            margin-bottom: 1.5rem;
            line-height: 1.6;
            color: var(--fg-secondary);
        }

        .connection-actions {
            display: flex;
            gap: 1rem;
        }

        .btn {
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 6px;
            font-family: 'Fira Code', monospace;
            font-weight: 500;
            cursor: pointer;
            transition: var(--transition);
            font-size: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .btn-primary {
            background: linear-gradient(45deg, var(--status-online), #8be9fd);
            color: var(--bg-primary);
            box-shadow: 0 2px 6px rgba(80, 250, 123, 0.3);
        }

        .btn-secondary {
            background: rgba(68, 71, 90, 0.7);
            color: var(--fg-primary);
            border: 1px solid var(--bg-secondary);
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }

        .btn:active {
            transform: translateY(0);
        }

        .terminal-controls {
            display: flex;
            gap: 0.5rem;
            margin-left: 1rem;
        }

        .control-btn {
            width: 24px;
            height: 24px;
            background: var(--bg-secondary);
            border: none;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            color: var(--fg-primary);
            font-size: 0.8rem;
            transition: var(--transition);
        }

        .control-btn:hover {
            background: var(--fg-secondary);
        }

        @media (max-width: 768px) {
            body {
                padding: 0.5rem;
            }
            
            .terminal-header {
                padding: 0.4rem 0.8rem;
                flex-direction: column;
                align-items: flex-start;
                gap: 0.5rem;
            }
            
            .connection-status {
                margin-left: auto;
            }
            
            .terminal-title {
                font-size: 0.95rem;
            }
        }
    </style>
</head>
<body>
    <header class="terminal-header">
        <div class="terminal-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
            <span>Web Terminal</span>
        </div>
        <div class="terminal-controls">
            <button class="control-btn" id="copy-btn" title="Copy terminal content">
                <span>📋</span>
            </button>
            <button class="control-btn" id="clear-btn" title="Clear terminal">
                <span>⌧</span>
            </button>
        </div>
        <div class="connection-status">
            <span class="status-indicator" id="status-indicator"></span>
            <span id="status-text">Disconnected</span>
        </div>
    </header>

    <main id="terminal-container"></main>

    <div class="terminal-overlay" id="connection-overlay">
        <div class="overlay-content">
            <h1 class="overlay-title">Terminal Connection</h1>
            <p class="overlay-message">
                Establishing secure connection to terminal server...
                <br>
                Please wait while we initialize your session.
            </p>
            <div class="connection-actions">
                <button class="btn btn-primary" id="reconnect-btn">
                    <span>⟳</span> Reconnect
                </button>
                <button class="btn btn-secondary" id="cancel-btn">
                    <span>✕</span> Cancel
                </button>
            </div>
        </div>
    </div>

    <!-- Xterm.js Scripts -->
    <script src="https://cdn.jsdelivr.net/npm/xterm@5.3.0/lib/xterm.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/xterm-addon-fit@0.8.0/lib/xterm-addon-fit.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/xterm-addon-web-links@0.8.0/lib/xterm-addon-web-links.min.js"></script>

    <script>
        // Constants and Configuration
        const CONFIG = {
            TERMINAL_THEME: {
                background: '#282a36',
                foreground: '#f8f8f2',
                cursor: '#f8f8f0',
                cursorAccent: '#44475a',
                selectionBackground: 'rgba(68, 71, 90, 0.8)',
                selectionForeground: '#f8f8f2',
                black: '#21222c',
                red: '#ff5555',
                green: '#50fa7b',
                yellow: '#f1fa8c',
                blue: '#bd93f9',
                magenta: '#ff79c6',
                cyan: '#8be9fd',
                white: '#f8f8f2',
                brightBlack: '#6272a4',
                brightRed: '#ff6e6e',
                brightGreen: '#69ff94',
                brightYellow: '#ffffa5',
                brightBlue: '#d6acff',
                brightMagenta: '#ff92df',
                brightCyan: '#a4ffff',
                brightWhite: '#ffffff'
            },
            WEBSOCKET_RECONNECT_DELAY: 3000,
            MAX_RECONNECT_ATTEMPTS: 5,
            DEBOUNCE_DELAY: 250
        };

        // DOM Elements
        const elements = {
            terminalContainer: document.getElementById('terminal-container'),
            statusIndicator: document.getElementById('status-indicator'),
            statusText: document.getElementById('status-text'),
            connectionOverlay: document.getElementById('connection-overlay'),
            reconnectBtn: document.getElementById('reconnect-btn'),
            cancelBtn: document.getElementById('cancel-btn'),
            copyBtn: document.getElementById('copy-btn'),
            clearBtn: document.getElementById('clear-btn')
        };

        // Terminal State
        let terminal = null;
        let fitAddon = null;
        let webLinksAddon = null;
        let websocket = null;
        let reconnectAttempts = 0;
        let isManuallyDisconnected = false;
        let resizeTimeout = null;

        // Initialize Terminal
        function initTerminal() {
            terminal = new Terminal({
                cursorBlink: true,
                fontFamily: 'Fira Code, monospace',
                fontSize: 14,
                lineHeight: 1.1,
                theme: CONFIG.TERMINAL_THEME,
                scrollback: 5000,
                tabStopWidth: 4,
                cursorStyle: 'block',
                cursorWidth: 2,
                allowTransparency: true,
                bellStyle: 'sound'
            });

            // Load addons
            fitAddon = new FitAddon.FitAddon();
            webLinksAddon = new WebLinksAddon.WebLinksAddon();
            
            terminal.loadAddon(fitAddon);
            terminal.loadAddon(webLinksAddon);

            // Open terminal
            terminal.open(elements.terminalContainer);
            fitAddon.fit();
            terminal.focus();

            // Setup terminal event listeners
            setupTerminalEvents();
        }

        // Setup Terminal Event Listeners
        function setupTerminalEvents() {
            // Copy terminal content
            elements.copyBtn.addEventListener('click', () => {
                if (terminal) {
                    navigator.clipboard.writeText(terminal.getSelection() || terminal.buffer.active.getLine(0)?.translateToString() || '')
                        .then(() => {
                            showNotification('📋 Content copied to clipboard!', 'success');
                        })
                        .catch(err => {
                            console.error('Failed to copy:', err);
                            showNotification('❌ Failed to copy content', 'error');
                        });
                }
            });

            // Clear terminal
            elements.clearBtn.addEventListener('click', () => {
                terminal?.clear();
                terminal?.focus();
            });

            // Handle user input
            terminal.onData(data => {
                if (websocket?.readyState === WebSocket.OPEN) {
                    websocket.send(data);
                } else {
                    showNotification('⚠️ Not connected to server', 'warning');
                }
            });

            // Handle paste events
            terminal.attachCustomKeyEventHandler(e => {
                if (e.ctrlKey && e.key === 'v') {
                    navigator.clipboard.readText().then(text => {
                        terminal.paste(text);
                    });
                    return false;
                }
                return true;
            });

            // Handle context menu for paste
            elements.terminalContainer.addEventListener('contextmenu', async (e) => {
                e.preventDefault();
                try {
                    const text = await navigator.clipboard.readText();
                    terminal.paste(text);
                } catch (err) {
                    console.error('Paste failed:', err);
                }
            });
        }

        // WebSocket Connection Management
        function createWebSocket() {
            const protocol = location.protocol === 'https:' ? 'wss://' : 'ws://';
            const wsUrl = `${protocol}${location.host}/ws`;
            
            return new WebSocket(wsUrl);
        }

        function setupWebSocket() {
            if (isManuallyDisconnected) return;

            elements.connectionOverlay.classList.remove('hidden');
            updateConnectionStatus('connecting', 'Connecting...');

            websocket = createWebSocket();

            websocket.onopen = () => {
                console.log('✅ WebSocket connection established');
                reconnectAttempts = 0;
                isManuallyDisconnected = false;
                
                updateConnectionStatus('online', 'Connected');
                elements.connectionOverlay.classList.add('hidden');
                
                // Send initial resize
                sendResizeEvent();
                
                // Send welcome message
                terminal?.write('\r\n\x1b[32m✨ Terminal connected successfully!\x1b[0m\r\n');
            };

            websocket.onclose = (event) => {
                console.log(`❌ WebSocket closed (code: ${event.code})`);
                
                if (!isManuallyDisconnected) {
                    updateConnectionStatus('offline', 'Disconnected');
                    handleReconnect();
                }
            };

            websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                updateConnectionStatus('offline', 'Connection error');
                showNotification('❌ WebSocket connection error', 'error');
            };

            websocket.onmessage = (event) => {
                if (terminal) {
                    try {
                        terminal.write(event.data);
                    } catch (err) {
                        console.error('Error writing to terminal:', err);
                        terminal.write('\r\n\x1b[31m⚠️ Error displaying terminal output\x1b[0m\r\n');
                    }
                }
            };
        }

        function handleReconnect() {
            if (reconnectAttempts >= CONFIG.MAX_RECONNECT_ATTEMPTS || isManuallyDisconnected) {
                elements.connectionOverlay.classList.remove('hidden');
                updateConnectionStatus('offline', 'Reconnect failed');
                showNotification(`❌ Max reconnect attempts reached (${CONFIG.MAX_RECONNECT_ATTEMPTS})`, 'error');
                return;
            }

            reconnectAttempts++;
            updateConnectionStatus('connecting', `Reconnecting (${reconnectAttempts}/${CONFIG.MAX_RECONNECT_ATTEMPTS})...`);
            showNotification(`🔄 Attempting to reconnect... (${reconnectAttempts}/${CONFIG.MAX_RECONNECT_ATTEMPTS})`, 'info');

            setTimeout(() => {
                setupWebSocket();
            }, CONFIG.WEBSOCKET_RECONNECT_DELAY);
        }

        function sendResizeEvent() {
            if (!websocket || websocket.readyState !== WebSocket.OPEN || !terminal) return;

            const dimensions = {
                type: 'resize',
                cols: terminal.cols,
                rows: terminal.rows
            };
            
            websocket.send(JSON.stringify(dimensions));
        }

        // UI Updates
        function updateConnectionStatus(status, text) {
            elements.statusText.textContent = text;
            elements.statusIndicator.className = 'status-indicator';
            
            switch(status) {
                case 'online':
                    elements.statusIndicator.classList.add('online');
                    break;
                case 'connecting':
                    elements.statusIndicator.classList.add('connecting');
                    break;
                case 'offline':
                    elements.statusIndicator.classList.add('offline');
                    break;
            }
        }

        function showNotification(message, type = 'info') {
            // Create notification element
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            notification.innerHTML = `<span class="notification-icon">${getNotificationIcon(type)}</span> ${message}`;
            
            // Style based on type
            const styles = {
                success: { background: '#3a5a40', borderLeft: '4px solid #588157' },
                error: { background: '#b93b3b', borderLeft: '4px solid #d90429' },
                warning: { background: '#d99d35', borderLeft: '4px solid #e9c46a' },
                info: { background: '#3a86ff', borderLeft: '4px solid #5e60ce' }
            };
            
            Object.assign(notification.style, {
                position: 'fixed',
                bottom: '20px',
                right: '20px',
                padding: '12px 20px',
                borderRadius: '6px',
                color: '#fff',
                fontSize: '14px',
                fontFamily: "'Fira Code', monospace",
                boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                zIndex: '1000',
                transform: 'translateX(200%)',
                transition: 'transform 0.3s ease-out',
                ...styles[type]
            });
            
            document.body.appendChild(notification);
            
            // Animate in
            setTimeout(() => {
                notification.style.transform = 'translateX(0)';
            }, 10);
            
            // Auto-remove after delay
            setTimeout(() => {
                notification.style.transform = 'translateX(200%)';
                setTimeout(() => notification.remove(), 300);
            }, 3000);
        }

        function getNotificationIcon(type) {
            const icons = {
                success: '✅',
                error: '❌',
                warning: '⚠️',
                info: 'ℹ️'
            };
            return icons[type] || 'ℹ️';
        }

        // Handle Window Events
        function setupWindowEvents() {
            // Resize handling with debounce
            window.addEventListener('resize', () => {
                if (resizeTimeout) clearTimeout(resizeTimeout);
                resizeTimeout = setTimeout(() => {
                    fitAddon?.fit();
                    sendResizeEvent();
                }, CONFIG.DEBOUNCE_DELAY);
            });

            // Reconnect button
            elements.reconnectBtn.addEventListener('click', () => {
                isManuallyDisconnected = false;
                reconnectAttempts = 0;
                setupWebSocket();
            });

            // Cancel button
            elements.cancelBtn.addEventListener('click', () => {
                isManuallyDisconnected = true;
                websocket?.close();
                elements.connectionOverlay.classList.add('hidden');
                terminal?.write('\r\n\x1b[33m⏹️ Connection cancelled by user\x1b[0m\r\n');
            });

            // Handle page unload
            window.addEventListener('beforeunload', () => {
                isManuallyDisconnected = true;
                websocket?.close();
            });
        }

        // Initialize Application
        function initApplication() {
            initTerminal();
            setupWindowEvents();
            setupWebSocket();
            
            // Initial focus
            setTimeout(() => {
                terminal?.focus();
            }, 500);
        }

        // Start the application when DOM is loaded
        document.addEventListener('DOMContentLoaded', initApplication);
    </script>
</body>
</html>
