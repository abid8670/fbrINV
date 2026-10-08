// FBR Digital Invoicing - Munshi AI (Conversational Tax & Accounting Copilot)
(function () {
    const defaultConfig = {
        enabled: true,
        language: 'ur-PK', // Default to Urdu for Pakistani business context
        speech_rate: 1.0,
        provider: 'browser'
    };

    const cfg = window.FBR_AI_VOICE_CONFIG || defaultConfig;
    let availableVoices = [];
    let recognition = null;
    let isListening = false;
    let chatHistory = [];

    // Load browser speech synthesis voices
    function populateVoices() {
        if ('speechSynthesis' in window) {
            availableVoices = window.speechSynthesis.getVoices();
        }
    }

    if ('speechSynthesis' in window) {
        populateVoices();
        window.speechSynthesis.onvoiceschanged = populateVoices;
    }

    // Initialize Web Speech Recognition (Mic Voice Input)
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = (cfg.language === 'en-US') ? 'en-US' : 'ur-PK';
    }

    function playBase64Audio(b64Audio) {
        try {
            const snd = new Audio("data:audio/mp3;base64," + b64Audio);
            return snd.play();
        } catch (e) {
            console.error("Audio playback error:", e);
        }
    }

    function speak(text, customLang = null) {
        if (!cfg.enabled) return;
        if (!('speechSynthesis' in window)) {
            console.warn('Text-to-Speech not supported.');
            return;
        }

        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        const targetLang = customLang || cfg.language || 'ur-PK';
        utterance.lang = targetLang;
        utterance.rate = cfg.speech_rate || 1.0;

        if (availableVoices.length === 0 && 'speechSynthesis' in window) {
            availableVoices = window.speechSynthesis.getVoices();
        }

        if (targetLang.startsWith('ur')) {
            const urVoice = availableVoices.find(v => v.lang.startsWith('ur') || v.lang.startsWith('hi'));
            if (urVoice) utterance.voice = urVoice;
        } else {
            const enVoice = availableVoices.find(v => 
                (v.lang.startsWith('en') && (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('Online')))
            ) || availableVoices.find(v => v.lang.startsWith('en'));
            if (enVoice) utterance.voice = enVoice;
        }

        window.speechSynthesis.speak(utterance);
    }

    // Expose globally
    window.fbrSpeak = speak;
    window.fbrPlayBase64 = playBase64Audio;

    document.addEventListener('DOMContentLoaded', function () {
        // 1. Speak Flash Messages on load
        const alerts = document.querySelectorAll('.alert');
        if (alerts.length > 0 && cfg.enabled) {
            let messageText = '';
            alerts.forEach(al => {
                const text = al.innerText.trim();
                if (text) messageText += text + '. ';
            });
            if (messageText) {
                setTimeout(() => { speak(messageText); }, 800);
            }
        }

        // 2. Inject Munshi AI Floating Widget & Offcanvas Modal
        injectMunshiAICopilot();
    });

    function injectMunshiAICopilot() {
        // Floating Launcher Pill
        const widget = document.createElement('div');
        widget.id = 'aiVoiceWidget';
        widget.className = 'position-fixed bottom-0 end-0 m-3 d-flex align-items-center gap-2 p-2 bg-dark text-white rounded-pill shadow-lg no-print';
        widget.style.zIndex = '1050';
        widget.style.border = '1px solid rgba(16, 185, 129, 0.4)';

        widget.innerHTML = `
            <button type="button" id="munshiOpenBtn" class="btn btn-sm btn-emerald text-white rounded-pill px-3 py-1 d-flex align-items-center gap-2 shadow-sm" title="Talk to Munshi AI Copilot">
                <i class="bi bi-mic-fill fs-6 animate-pulse"></i>
                <span class="fw-bold" style="font-size: 0.8rem;">Munshi AI</span>
            </button>
            <button type="button" id="aiReadPageBtn" class="btn btn-sm btn-outline-light rounded-pill py-0 px-2 fs-xs me-1" title="Read Page Summary">
                <i class="bi bi-volume-up me-1"></i> Summary
            </button>
        `;
        document.body.appendChild(widget);

        // Munshi AI Interactive Chat/Voice Drawer
        const modalContainer = document.createElement('div');
        modalContainer.id = 'munshiAiModal';
        modalContainer.className = 'position-fixed bottom-0 end-0 m-3 shadow-2xl bg-white border rounded-4 d-none no-print';
        modalContainer.style.zIndex = '1060';
        modalContainer.style.width = '380px';
        modalContainer.style.maxWidth = '92vw';
        modalContainer.style.maxHeight = '85vh';
        modalContainer.style.boxShadow = '0 20px 40px -15px rgba(0,0,0,0.3)';
        modalContainer.style.display = 'flex';
        modalContainer.style.flexDirection = 'column';
        modalContainer.style.overflow = 'hidden';

        modalContainer.innerHTML = `
            <!-- Header -->
            <div class="p-3 bg-emerald text-white d-flex align-items-center justify-content-between">
                <div class="d-flex align-items-center gap-2">
                    <div class="rounded-circle bg-white text-emerald p-2 d-flex align-items-center justify-content-center" style="width: 38px; height: 38px;">
                        <i class="bi bi-person-badge-fill fs-5"></i>
                    </div>
                    <div>
                        <h6 class="m-0 fw-bold fs-sm">Munshi AI (منشی صاحب)</h6>
                        <small class="text-white-50 fs-xs d-flex align-items-center gap-1">
                            <span class="badge bg-success p-1 rounded-circle" style="width: 7px; height: 7px;"></span>
                            FBR Tax & Business Copilot
                        </small>
                    </div>
                </div>
                <div class="d-flex align-items-center gap-1">
                    <button type="button" id="munshiMuteBtn" class="btn btn-sm btn-emerald text-white p-1" title="Toggle Voice Mute">
                        <i class="bi bi-volume-up-fill fs-6"></i>
                    </button>
                    <button type="button" id="munshiCloseBtn" class="btn btn-sm btn-emerald text-white p-1">
                        <i class="bi bi-x-lg fs-6"></i>
                    </button>
                </div>
            </div>

            <!-- Chat Message Stream -->
            <div id="munshiChatBody" class="p-3 overflow-y-auto flex-grow-1" style="height: 340px; background-color: #f8fafc; font-size: 0.85rem;">
                <div class="d-flex gap-2 mb-3">
                    <div class="bg-emerald text-white rounded-circle p-1 d-flex align-items-center justify-content-center flex-shrink-0" style="width: 28px; height: 28px;">
                        <i class="bi bi-robot fs-6"></i>
                    </div>
                    <div class="p-2.5 rounded-3 bg-white border text-dark shadow-xs" style="max-width: 85%;">
                        Aadaab! Main aapka <b>Munshi AI</b> hoon. Aap mujhse bol kar ya likh kar aaj ki sales, tax, top customers, ya FBR rules ke baray mein kuch bhi pooch sakte hain.
                    </div>
                </div>

                <!-- Quick Query Chips -->
                <div class="d-flex flex-wrap gap-1 mb-2 mt-2">
                    <button type="button" class="btn btn-xs btn-outline-dark rounded-pill py-0 px-2 munshi-chip" data-q="Aaj ki sales aur tax kitna hai?">
                        📊 Aaj ki Sales
                    </button>
                    <button type="button" class="btn btn-xs btn-outline-dark rounded-pill py-0 px-2 munshi-chip" data-q="Kul kitna sales tax jama hua?">
                        💰 Tax Summary
                    </button>
                    <button type="button" class="btn btn-xs btn-outline-dark rounded-pill py-0 px-2 munshi-chip" data-q="Top customer kon hai?">
                        👥 Top Customer
                    </button>
                    <button type="button" class="btn btn-xs btn-outline-dark rounded-pill py-0 px-2 munshi-chip" data-q="FBR SRO 350 rule samjhao">
                        📜 SRO 350 Rule
                    </button>
                </div>
            </div>

            <!-- Listening Status Banner -->
            <div id="munshiVoiceStatus" class="px-3 py-1 bg-warning-subtle text-warning-emphasis fs-xs fw-semibold d-none align-items-center gap-2">
                <span class="spinner-grow spinner-grow-sm text-danger" role="status"></span>
                <span>Main sun raha hoon, boliye... (Listening...)</span>
            </div>

            <!-- Voice & Input Bar -->
            <div class="p-2 bg-white border-top">
                <form id="munshiChatForm" class="d-flex align-items-center gap-2 m-0">
                    <button type="button" id="munshiMicBtn" class="btn btn-outline-danger rounded-circle p-2 d-flex align-items-center justify-content-center flex-shrink-0" style="width: 38px; height: 38px;" title="Click & Speak (Microphone)">
                        <i class="bi bi-mic-fill fs-5"></i>
                    </button>
                    <input type="text" id="munshiInput" class="form-control form-control-sm rounded-pill px-3" placeholder="Bol kar ya likh kar poochein..." autocomplete="off">
                    <button type="submit" class="btn btn-emerald text-white rounded-circle p-2 d-flex align-items-center justify-content-center flex-shrink-0" style="width: 38px; height: 38px;">
                        <i class="bi bi-send-fill fs-6"></i>
                    </button>
                </form>
            </div>
        `;
        document.body.appendChild(modalContainer);

        // Attach event listeners
        const openBtn = document.getElementById('munshiOpenBtn');
        const closeBtn = document.getElementById('munshiCloseBtn');
        const muteBtn = document.getElementById('munshiMuteBtn');
        const micBtn = document.getElementById('munshiMicBtn');
        const chatForm = document.getElementById('munshiChatForm');
        const chatInput = document.getElementById('munshiInput');
        const readBtn = document.getElementById('aiReadPageBtn');

        openBtn.addEventListener('click', function () {
            modalContainer.classList.toggle('d-none');
            if (!modalContainer.classList.contains('d-none')) {
                chatInput.focus();
            }
        });

        closeBtn.addEventListener('click', function () {
            modalContainer.classList.add('d-none');
            if (recognition && isListening) recognition.stop();
        });

        muteBtn.addEventListener('click', function () {
            cfg.enabled = !cfg.enabled;
            if (!cfg.enabled) {
                window.speechSynthesis.cancel();
                muteBtn.innerHTML = '<i class="bi bi-volume-mute-fill fs-6"></i>';
                muteBtn.classList.replace('btn-emerald', 'btn-secondary');
            } else {
                muteBtn.innerHTML = '<i class="bi bi-volume-up-fill fs-6"></i>';
                muteBtn.classList.replace('btn-secondary', 'btn-emerald');
                speak(cfg.language === 'ur-PK' ? "Aawaz active hai." : "Voice enabled.");
            }
        });

        readBtn.addEventListener('click', readPageSummary);

        // Quick Chips click
        document.querySelectorAll('.munshi-chip').forEach(btn => {
            btn.addEventListener('click', function () {
                const q = this.getAttribute('data-q');
                submitCopilotQuery(q);
            });
        });

        // Form Submit
        chatForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const text = chatInput.value.trim();
            if (text) {
                chatInput.value = '';
                submitCopilotQuery(text);
            }
        });

        // Microphone Speech Recognition
        if (recognition) {
            recognition.onstart = function () {
                isListening = true;
                micBtn.className = 'btn btn-danger text-white rounded-circle p-2 d-flex align-items-center justify-content-center flex-shrink-0 animate-pulse';
                document.getElementById('munshiVoiceStatus').classList.remove('d-none');
                document.getElementById('munshiVoiceStatus').classList.add('d-flex');
            };

            recognition.onend = function () {
                isListening = false;
                micBtn.className = 'btn btn-outline-danger rounded-circle p-2 d-flex align-items-center justify-content-center flex-shrink-0';
                document.getElementById('munshiVoiceStatus').classList.add('d-none');
                document.getElementById('munshiVoiceStatus').classList.remove('d-flex');
            };

            recognition.onresult = function (event) {
                const transcript = event.results[0][0].transcript;
                if (transcript) {
                    submitCopilotQuery(transcript);
                }
            };

            recognition.onerror = function (event) {
                console.warn('Speech recognition error:', event.error);
                isListening = false;
                micBtn.className = 'btn btn-outline-danger rounded-circle p-2 d-flex align-items-center justify-content-center flex-shrink-0';
                document.getElementById('munshiVoiceStatus').classList.add('d-none');
                document.getElementById('munshiVoiceStatus').classList.remove('d-flex');
            };

            micBtn.addEventListener('click', function () {
                if (isListening) {
                    recognition.stop();
                } else {
                    recognition.lang = (cfg.language === 'en-US') ? 'en-US' : 'ur-PK';
                    recognition.start();
                }
            });
        } else {
            micBtn.disabled = true;
            micBtn.title = "Speech recognition is not supported in this browser. Please type your query.";
        }
    }

    function submitCopilotQuery(queryText) {
        const chatBody = document.getElementById('munshiChatBody');
        
        // 1. Append User Bubble
        const userDiv = document.createElement('div');
        userDiv.className = 'd-flex justify-content-end mb-3';
        userDiv.innerHTML = `
            <div class="p-2.5 rounded-3 bg-emerald text-white shadow-xs" style="max-width: 85%;">
                ${escapeHtml(queryText)}
            </div>
        `;
        chatBody.appendChild(userDiv);
        chatBody.scrollTop = chatBody.scrollHeight;

        // 2. Append Typing Placeholder
        const typingDiv = document.createElement('div');
        typingDiv.id = 'munshiTypingIndicator';
        typingDiv.className = 'd-flex gap-2 mb-3';
        typingDiv.innerHTML = `
            <div class="bg-emerald text-white rounded-circle p-1 d-flex align-items-center justify-content-center flex-shrink-0" style="width: 28px; height: 28px;">
                <i class="bi bi-robot fs-6"></i>
            </div>
            <div class="p-2.5 rounded-3 bg-white border text-muted shadow-xs d-flex align-items-center gap-2">
                <span class="spinner-border spinner-border-sm text-emerald"></span>
                <span>Munshi AI hisaab kar raha hai...</span>
            </div>
        `;
        chatBody.appendChild(typingDiv);
        chatBody.scrollTop = chatBody.scrollHeight;

        // 3. Send Query with History to Backend Copilot API
        const historyPayload = chatHistory.slice(-6);
        chatHistory.push({ role: 'user', text: queryText });

        fetch('/api/ai/copilot', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                query: queryText,
                history: historyPayload,
                language: cfg.language || 'ur-PK'
            })
        })
        .then(r => r.json())
        .then(data => {
            const typing = document.getElementById('munshiTypingIndicator');
            if (typing) typing.remove();

            if (data.success) {
                // Record model response into history
                chatHistory.push({ role: 'model', text: data.reply });

                // Append AI Response Bubble
                const botDiv = document.createElement('div');
                botDiv.className = 'd-flex gap-2 mb-3';
                
                let actionHtml = '';
                if (data.action && data.action.url) {
                    actionHtml = `
                        <div class="mt-2 pt-2 border-top">
                            <a href="${data.action.url}" class="btn btn-xs btn-emerald text-white rounded-pill px-3 py-1">
                                <i class="bi bi-arrow-right-circle me-1"></i> ${data.action.label || 'Open'}
                            </a>
                        </div>
                    `;
                }

                botDiv.innerHTML = `
                    <div class="bg-emerald text-white rounded-circle p-1 d-flex align-items-center justify-content-center flex-shrink-0" style="width: 28px; height: 28px;">
                        <i class="bi bi-robot fs-6"></i>
                    </div>
                    <div class="p-2.5 rounded-3 bg-white border text-dark shadow-xs" style="max-width: 85%;">
                        <div class="munshi-reply-content">${formatReplyMarkdown(data.reply)}</div>
                        ${actionHtml}
                        <div class="mt-1 d-flex justify-content-end">
                            <button type="button" class="btn btn-xs btn-link p-0 text-muted replay-voice-btn" title="Replay Voice">
                                <i class="bi bi-volume-up"></i>
                            </button>
                        </div>
                    </div>
                `;
                chatBody.appendChild(botDiv);
                chatBody.scrollTop = chatBody.scrollHeight;

                // Replay voice handler
                botDiv.querySelector('.replay-voice-btn').addEventListener('click', () => {
                    speak(data.text_to_speak || data.reply, data.language || cfg.language);
                });

                // Automatically speak response
                if (cfg.enabled) {
                    speak(data.text_to_speak || data.reply, data.language || cfg.language);
                }
            } else {
                appendBotError(data.reply || "Kuch masla hua, baraye meherbani dobara try karein.");
            }
        })
        .catch(err => {
            const typing = document.getElementById('munshiTypingIndicator');
            if (typing) typing.remove();
            appendBotError("Connection error: " + err.message);
        });
    }

    function appendBotError(errMsg) {
        const chatBody = document.getElementById('munshiChatBody');
        const botDiv = document.createElement('div');
        botDiv.className = 'd-flex gap-2 mb-3';
        botDiv.innerHTML = `
            <div class="bg-danger text-white rounded-circle p-1 d-flex align-items-center justify-content-center flex-shrink-0" style="width: 28px; height: 28px;">
                <i class="bi bi-exclamation-triangle fs-6"></i>
            </div>
            <div class="p-2.5 rounded-3 bg-danger-subtle text-danger border shadow-xs" style="max-width: 85%;">
                ${escapeHtml(errMsg)}
            </div>
        `;
        chatBody.appendChild(botDiv);
        chatBody.scrollTop = chatBody.scrollHeight;
    }

    function readPageSummary() {
        const title = document.querySelector('h4, h5, h6')?.innerText || 'FBR Digital Invoicing';
        const isUrdu = cfg.language === 'ur-PK';

        const totalInvoicesEl = document.querySelector('.stat-card h3');
        if (totalInvoicesEl) {
            const count = totalInvoicesEl.innerText;
            speak(isUrdu ? `Dashboard khula hai. Kul invoices ${count} hain.` : `Dashboard overview. Total invoices: ${count}.`);
            return;
        }

        const invNoEl = document.querySelector('h3.font-mono');
        if (invNoEl) {
            const invNo = invNoEl.innerText;
            const buyerEl = document.querySelector('.card-body h5')?.innerText || 'Customer';
            const totalEl = document.querySelector('.text-emerald.font-mono')?.innerText || 'PKR 0';
            speak(isUrdu ? `Invoice number ${invNo}. Buyer ${buyerEl}. Grand Total ${totalEl}.` : `Invoice ${invNo} for ${buyerEl}. Grand Total is ${totalEl}.`);
            return;
        }

        speak(isUrdu ? `Aap is waqt ${title} page dekh rahe hain.` : `You are viewing ${title}.`);
    }

    function escapeHtml(str) {
        return str.replace(/[&<>"']/g, function (m) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m];
        });
    }

    function formatReplyMarkdown(text) {
        return text
            .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
            .replace(/\*(.*?)\*/g, '<i>$1</i>')
            .replace(/\n/g, '<br>');
    }
})();
