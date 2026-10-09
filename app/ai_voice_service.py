import os
import requests
import base64

class AIVoiceService:
    _cached_model = None  # Cache tuple (api_version, model_name) once confirmed

    # High-priority active models across Google AI Studio tiers
    PREFERRED_MODELS = [
        'gemini-flash-lite-latest',
        'gemini-3.8-flash',
        'gemini-3.5-flash',
        'gemini-3.5-flash-lite',
        'gemini-3.1-flash-lite',
        'gemini-flash-latest',
        'gemma-4-26b-a4b-it',
        'gemini-2.0-flash',
        'gemini-1.5-flash'
    ]

    @staticmethod
    def _find_candidate_models(api_key):
        """
        Dynamically queries Google ModelService to get all available models
        supporting generateContent for this key, ordered by performance.
        """
        candidates = []
        for api_ver in ['v1beta', 'v1']:
            list_url = f"https://generativelanguage.googleapis.com/{api_ver}/models?key={api_key}"
            try:
                resp = requests.get(list_url, timeout=6)
                if resp.status_code == 200:
                    models_data = resp.json().get('models', [])
                    gen_models = [
                        m.get('name') for m in models_data 
                        if 'generateContent' in m.get('supportedGenerationMethods', [])
                    ]
                    # Sort candidates according to PREFERRED_MODELS order
                    for pref in AIVoiceService.PREFERRED_MODELS:
                        for gm in gen_models:
                            if pref in gm and (api_ver, gm) not in candidates:
                                candidates.append((api_ver, gm))
                    
                    # Add any remaining generateContent models as fallback
                    for gm in gen_models:
                        if (api_ver, gm) not in candidates:
                            candidates.append((api_ver, gm))
                    if candidates:
                        break
            except Exception:
                continue

        # If ListModels couldn't be reached, supply hardcoded defaults
        if not candidates:
            for m in AIVoiceService.PREFERRED_MODELS:
                candidates.append(('v1beta', f"models/{m}"))

        return candidates

    @staticmethod
    def test_voice_api(provider, api_key, language='en-US', sample_text=None):
        """
        Validates API keys and tests synthesis/response.
        Supports Google AI Studio (Gemini), Google Cloud TTS, OpenAI, and Browser.
        """
        provider = (provider or 'browser').lower().strip()
        api_key = (api_key or '').strip()

        if not sample_text:
            if language == 'ur-PK':
                sample_text = "FiscalSync DI Voice Assistant mein aapka khush amdeed. Humara AI Voice Assistant online aur active hai."
            else:
                sample_text = "Welcome to FiscalSync DI. Enterprise AI Voice Assistant is online and ready."

        if provider == 'browser' or not api_key:
            return {
                'success': True,
                'provider': 'browser',
                'message': 'Native Browser Speech Synthesis is active (Free, zero configuration required).',
                'text_to_speak': sample_text,
                'audio_base64': None
            }

        # 1. Google AI Studio (Gemini API)
        if provider in ['google_ai_studio', 'gemini']:
            return AIVoiceService._test_gemini(api_key, language, sample_text)

        # 2. Google Cloud Neural TTS
        elif provider in ['google_tts', 'google']:
            tts_res = AIVoiceService._test_google_cloud_tts(api_key, language, sample_text)
            if tts_res['success']:
                return tts_res
            
            # If Google Cloud TTS failed, test if user supplied a Google AI Studio key
            gemini_res = AIVoiceService._test_gemini(api_key, language, sample_text)
            if gemini_res['success']:
                return {
                    'success': True,
                    'provider': 'google_ai_studio',
                    'message': 'Detected Google AI Studio (Gemini) API Key! Connected successfully. AI Voice is active.',
                    'text_to_speak': gemini_res.get('text_to_speak', sample_text),
                    'audio_base64': None,
                    'is_gemini_detected': True
                }
            
            return {
                'success': False,
                'provider': 'google_tts',
                'message': tts_res['message'] + " (Tip: Agar yeh key aistudio.google.com se li hai to Provider mein 'Google AI Studio (Gemini)' select karein)."
            }

        # 3. OpenAI TTS
        elif provider == 'openai':
            return AIVoiceService._test_openai_tts(api_key, language, sample_text)

        return {
            'success': False,
            'message': f"Unsupported voice provider: {provider}"
        }

    @staticmethod
    def _test_gemini(api_key, language, sample_text):
        """Tests Google AI Studio (Gemini) API key with dynamic candidate fallback."""
        candidates = AIVoiceService._find_candidate_models(api_key)
        
        # If we already have a confirmed cached working model, try it first
        if AIVoiceService._cached_model and AIVoiceService._cached_model in candidates:
            candidates.remove(AIVoiceService._cached_model)
            candidates.insert(0, AIVoiceService._cached_model)

        prompt = (
            "Say in one short sentence: 'FiscalSync DI Assistant is active and ready.' "
            if language != 'ur-PK'
            else "Urdu mein aik mukhtasar jumla kahein: 'FiscalSync DI Voice Assistant active aur ready hai.'"
        )
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "maxOutputTokens": 60,
                "temperature": 0.4
            }
        }

        last_error = None
        for v, m in candidates:
            model_path = m if m.startswith('models/') else f"models/{m}"
            url = f"https://generativelanguage.googleapis.com/{v}/{model_path}:generateContent?key={api_key}"
            try:
                resp = requests.post(url, json=payload, timeout=6)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates_list = data.get('candidates', [])
                    reply = ""
                    if candidates_list:
                        parts = candidates_list[0].get('content', {}).get('parts', [])
                        if parts:
                            reply = parts[0].get('text', '').strip()
                    
                    if not reply:
                        reply = sample_text
                    
                    # Cache this model for subsequent voice queries
                    AIVoiceService._cached_model = (v, model_path)
                    clean_model_name = model_path.replace('models/', '')

                    return {
                        'success': True,
                        'provider': 'google_ai_studio',
                        'message': f"Google AI Studio ({clean_model_name}) Connected Successfully! AI Voice is active.",
                        'text_to_speak': reply,
                        'audio_base64': None
                    }
                else:
                    err_data = resp.json().get('error', {})
                    last_error = f"Google AI Studio ({m}): {err_data.get('message', resp.text)}"
            except Exception as e:
                last_error = f"Connection to {m}: {str(e)}"

        return {
            'success': False,
            'provider': 'google_ai_studio',
            'message': last_error or "Could not connect to Google AI Studio models."
        }

    @staticmethod
    def _test_google_cloud_tts(api_key, language, text):
        """Synthesizes audio via Google Cloud Text-to-Speech API."""
        url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"
        
        lang_code = "ur-PK" if language == 'ur-PK' else "en-US"
        voice_name = "ur-PK-Wavenet-A" if language == 'ur-PK' else "en-US-Neural2-F"
        
        payload = {
            "input": {"text": text},
            "voice": {
                "languageCode": lang_code,
                "name": voice_name
            },
            "audioConfig": {
                "audioEncoding": "MP3",
                "speakingRate": 1.0
            }
        }

        try:
            resp = requests.post(url, json=payload, timeout=8)
            if resp.status_code == 200:
                audio_content = resp.json().get('audioContent')
                return {
                    'success': True,
                    'provider': 'google_cloud_tts',
                    'message': "Google Cloud Neural TTS synthesized audio successfully!",
                    'audio_base64': audio_content,
                    'text_to_speak': text
                }
            else:
                err_data = resp.json().get('error', {})
                msg = err_data.get('message', resp.text)
                return {
                    'success': False,
                    'provider': 'google_tts',
                    'message': f"Google Cloud TTS API Error ({resp.status_code}): {msg}"
                }
        except Exception as e:
            return {
                'success': False,
                'provider': 'google_tts',
                'message': f"Connection error to Google Cloud TTS: {str(e)}"
            }

    @staticmethod
    def _test_openai_tts(api_key, language, text):
        """Tests OpenAI Text-to-Speech API."""
        url = "https://api.openai.com/v1/audio/speech"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "tts-1",
            "input": text,
            "voice": "alloy"
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            if resp.status_code == 200:
                audio_base64 = base64.b64encode(resp.content).decode('utf-8')
                return {
                    'success': True,
                    'provider': 'openai',
                    'message': "OpenAI Neural TTS generated audio successfully!",
                    'audio_base64': audio_base64,
                    'text_to_speak': text
                }
            else:
                msg = resp.json().get('error', {}).get('message', resp.text)
                return {
                    'success': False,
                    'provider': 'openai',
                    'message': f"OpenAI Error ({resp.status_code}): {msg}"
                }
        except Exception as e:
            return {
                'success': False,
                'provider': 'openai',
                'message': f"Connection error to OpenAI: {str(e)}"
            }

    @staticmethod
    def ask_ai_assistant(query, context="", language='en-US', api_key=""):
        """Generates natural bilingual explanation from Gemini AI if key is present."""
        if not api_key:
            return None

        candidates = AIVoiceService._find_candidate_models(api_key)
        if AIVoiceService._cached_model and AIVoiceService._cached_model in candidates:
            candidates.remove(AIVoiceService._cached_model)
            candidates.insert(0, AIVoiceService._cached_model)

        system_instruction = (
            "You are the AI Voice Assistant for an FBR Digital Invoicing & Sales Tax System in Pakistan. "
            "Keep responses strictly within 1 to 2 clear sentences so they can be spoken via voice. "
            f"Respond in {'Urdu (Roman Urdu or Urdu script)' if language == 'ur-PK' else 'English'}."
        )

        prompt = f"{system_instruction}\n\nContext: {context}\n\nQuestion: {query}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 100, "temperature": 0.3}
        }

        for v, m in candidates:
            model_path = m if m.startswith('models/') else f"models/{m}"
            url = f"https://generativelanguage.googleapis.com/{v}/{model_path}:generateContent?key={api_key}"
            try:
                resp = requests.post(url, json=payload, timeout=6)
                if resp.status_code == 200:
                    candidates_list = resp.json().get('candidates', [])
                    if candidates_list:
                        parts = candidates_list[0].get('content', {}).get('parts', [])
                        if parts:
                            AIVoiceService._cached_model = (v, model_path)
                            return parts[0].get('text', '').strip()
            except Exception:
                continue

        return None

    @staticmethod
    def ask_copilot(query, context="", language='ur-PK', api_key="", history=None):
        """
        Interactive FBR Business Accountant / Munshi AI Copilot with multi-turn memory.
        Answers user questions conversationally with live business metrics.
        """
        if not api_key:
            return None

        candidates = AIVoiceService._find_candidate_models(api_key)
        if AIVoiceService._cached_model and AIVoiceService._cached_model in candidates:
            candidates.remove(AIVoiceService._cached_model)
            candidates.insert(0, AIVoiceService._cached_model)

        system_instruction = (
            "You are 'Munshi AI' (منشی صاحب), an expert, sharp, and friendly Pakistani Business Accountant and FBR Sales Tax Copilot. "
            "You work inside 'FiscalSync DI' - the Enterprise FBR Digital Invoicing & Billing Software in Pakistan.\n"
            "CRITICAL CONVERSATIONAL RULES:\n"
            "1. NO REPETITIVE GREETINGS: Only greet ('Aadaab' / 'Salam') in the very FIRST turn of a conversation. "
            "In ongoing conversations or follow-up questions, NEVER start with 'Aadaab' or 'Jee janab' every time! Jump straight into the direct, natural answer.\n"
            "2. CONVERSATION MEMORY: Maintain full memory of earlier questions and answers. If the user asks follow-up questions like 'aur tax kitna?', 'unka naam kya tha?', or 'is maheenay ka batao', refer back directly to the previous context.\n"
            "3. ACCURACY: Always use the provided [BUSINESS LIVE DATA] to state exact numbers (sales, tax, customer names, invoice counts).\n"
            "4. BREVITY: Keep answers conversational, natural, and concise (2 to 3 sentences maximum) for audio speech playback.\n"
            f"Respond in {'Roman Urdu / Urdu' if language == 'ur-PK' else 'English'}."
        )

        contents = []
        if history and isinstance(history, list) and len(history) > 0:
            # Build alternating multi-turn history with system instruction attached to the first anchor
            contents.append({
                "role": "user",
                "parts": [{"text": f"[SYSTEM RULES & LIVE METRICS]\n{system_instruction}\n\n{context}\n\nPlease assist me with my accounting."}]
            })
            contents.append({
                "role": "model",
                "parts": [{"text": "Samajh gaya. Main Munshi AI hoon, aapke business accounts aur FBR tax sawalat ke liye tayyar hoon."}]
            })
            for turn in history[-6:]:
                role = "user" if turn.get('role') == 'user' else "model"
                text = turn.get('text', '').strip()
                if text:
                    contents.append({"role": role, "parts": [{"text": text}]})
            contents.append({"role": "user", "parts": [{"text": query}]})
        else:
            prompt = f"{system_instruction}\n\n{context}\n\nUser Question: {query}"
            contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {"maxOutputTokens": 200, "temperature": 0.3}
        }

        for v, m in candidates:
            model_path = m if m.startswith('models/') else f"models/{m}"
            url = f"https://generativelanguage.googleapis.com/{v}/{model_path}:generateContent?key={api_key}"
            try:
                resp = requests.post(url, json=payload, timeout=7)
                if resp.status_code == 200:
                    candidates_list = resp.json().get('candidates', [])
                    if candidates_list:
                        parts = candidates_list[0].get('content', {}).get('parts', [])
                        if parts:
                            AIVoiceService._cached_model = (v, model_path)
                            return parts[0].get('text', '').strip()
            except Exception:
                continue

        return None
