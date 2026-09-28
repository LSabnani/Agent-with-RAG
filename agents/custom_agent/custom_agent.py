import os
import json
import time
import re
from datetime import datetime, timezone
import requests

class CustomAgent:
    def __init__(self, doc_rag_url="http://doc_rag:8003", tools_url="http://tools:8005", logging_url="http://logging:8006", gemini_api_key=None):
        self.doc_rag_url = doc_rag_url
        self.tools_url = tools_url
        self.logging_url = logging_url
        self.gemini_api_key = gemini_api_key or os.environ.get("GEMINI_API_KEY", "")

    def _resolve(self, url, host, port):
        if not os.environ.get("RUNNING_IN_DOCKER") and f"{host}:{port}" in url:
            return url.replace(f"{host}:{port}", f"127.0.0.1:{port}")
        return url

    def log(self, invoker, recipient, event_type, desc, payload, conv_id=None, status="success", dur_ms=0, in_tok=0, out_tok=0, model=None, is_error=False):
        try:
            url = self._resolve(self.logging_url, "logging", 8006)
            requests.post(f"{url}/api/logs", json={
                "invoker": invoker,
                "recipient": recipient,
                "conversation_id": conv_id,
                "type": event_type,
                "short_description": desc,
                "payload": payload,
                "status": status,
                "duration_ms": dur_ms,
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "model": model,
                "is_error": is_error,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, timeout=2)
        except Exception:
            pass

    def call_llm(self, prompt, system_instruction=None, model="gemma-4-26b-a4b-it", temperature=0.7, max_tokens=2048, custom_endpoint=None, conv_id=None):
        start_time = time.time()
        
        # If custom OpenAI-compatible endpoint specified
        if custom_endpoint:
            try:
                headers = {"Content-Type": "application/json"}
                msgs = []
                if system_instruction:
                    msgs.append({"role": "system", "content": system_instruction})
                msgs.append({"role": "user", "content": prompt})

                payload = {
                    "model": model,
                    "messages": msgs,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
                resp = requests.post(custom_endpoint, json=payload, headers=headers, timeout=30)
                dur_ms = int((time.time() - start_time) * 1000)
                res_json = resp.json()
                text = res_json.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                usage = res_json.get("usage", {})
                in_tok = usage.get("prompt_tokens", len(prompt) // 4)
                out_tok = usage.get("completion_tokens", len(text) // 4)

                self.log(
                    invoker="Custom Agent",
                    recipient="Custom LLM",
                    event_type="llm_call",
                    desc=f"Called Custom Endpoint: {model}",
                    payload={"prompt": prompt, "system": system_instruction, "response": text},
                    conv_id=conv_id,
                    dur_ms=dur_ms,
                    in_tok=in_tok,
                    out_tok=out_tok,
                    model=model
                )
                return text, in_tok, out_tok, dur_ms
            except Exception as e:
                dur_ms = int((time.time() - start_time) * 1000)
                self.log("Custom Agent", "Custom LLM", "llm_error", f"Error calling custom LLM: {e}", {"error": str(e)}, conv_id, "error", dur_ms, is_error=True)
                return f"Error contacting custom model: {e}", 0, 0, dur_ms

        # Google Gemini AI Studio client
        if self.gemini_api_key:
            try:
                from google import genai
                from google.genai import types
                client = genai.Client(api_key=self.gemini_api_key)
                
                config_params = {
                    "temperature": temperature,
                    "max_output_tokens": max_tokens
                }
                if system_instruction:
                    config_params["system_instruction"] = system_instruction

                resp = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(**config_params)
                )
                dur_ms = int((time.time() - start_time) * 1000)
                text = resp.text or ""

                # Token usage
                usage_meta = getattr(resp, "usage_metadata", None)
                in_tok = getattr(usage_meta, "prompt_token_count", len(prompt) // 4) or (len(prompt) // 4)
                out_tok = getattr(usage_meta, "candidates_token_count", len(text) // 4) or (len(text) // 4)

                self.log(
                    invoker="Custom Agent",
                    recipient="LLM",
                    event_type="llm_call",
                    desc=f"Generated content via Google GenAI ({model})",
                    payload={"prompt": prompt, "system_instruction": system_instruction, "response": text},
                    conv_id=conv_id,
                    dur_ms=dur_ms,
                    in_tok=in_tok,
                    out_tok=out_tok,
                    model=model
                )
                return text, in_tok, out_tok, dur_ms
            except Exception as e:
                dur_ms = int((time.time() - start_time) * 1000)
                self.log("Custom Agent", "LLM", "llm_error", f"Gemini API error: {e}", {"error": str(e)}, conv_id, "error", dur_ms, is_error=True)
                # Fallback to local simulation if key or quota issue
                return self._fallback_assistant_response(prompt, system_instruction), 50, 100, dur_ms

        # Fallback simulation if no API key configured
        dur_ms = int((time.time() - start_time) * 1000)
        return self._fallback_assistant_response(prompt, system_instruction), 50, 100, dur_ms

    def _fallback_assistant_response(self, prompt, system_instruction):
        return f"Synthesized answer based on available context and tools:\n\n{prompt[-300:] if len(prompt) > 300 else prompt}"

    def run(self, message, conversation_id, model="gemma-4-26b-a4b-it", temperature=0.7, max_tokens=2048,
            max_turns=3, skill_selector="Vector Store Selects", skill_threshold=0.2, doc_threshold=0.3,
            max_chunks=5, custom_endpoint=None, api_key=None):
        
        agent_start = time.time()
        steps = []
        max_turns = max(1, min(int(max_turns or 3), 10))

        # Initial Agent Invocaton Log
        self.log(
            invoker="Web UI",
            recipient="Custom Agent",
            event_type="chat_request",
            desc=f"User query received: '{message[:50]}...'",
            payload={
                "message": message,
                "agent_type": "Custom Agent",
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "max_turns": max_turns,
                "skill_selector": skill_selector
            },
            conv_id=conversation_id
        )

        steps.append({
            "component": "Agent",
            "icon": "🤖",
            "title": "Agent Initialized",
            "description": f"Processing query with {skill_selector} (Max turns: {max_turns})",
            "elapsed_ms": int((time.time() - agent_start) * 1000)
        })

        matched_skills = []

        # 1. Skill Selection
        s_start = time.time()
        if skill_selector == "Vector Store Selects":
            # Query doc_RAG skill vector store
            try:
                rag_url = self._resolve(self.doc_rag_url, "doc_rag", 8003)
                resp = requests.post(f"{rag_url}/api/rag/query", json={
                    "db_type": "skill",
                    "query": message,
                    "threshold": skill_threshold,
                    "limit": 2,
                    "conversation_id": conversation_id,
                    "api_key": api_key
                }, timeout=5)
                if resp.status_code == 200:
                    matched_skills = resp.json().get("results", [])
            except Exception as e:
                pass
            
            steps.append({
                "component": "Skills",
                "icon": "⚡",
                "title": "Skills Vector Search",
                "description": f"Retrieved {len(matched_skills)} skills matching threshold {skill_threshold}",
                "elapsed_ms": int((time.time() - s_start) * 1000),
                "data": matched_skills
            })

        elif skill_selector == "Use AI Agent with Tools":
            # Ask LLM to pick appropriate skill
            steps.append({
                "component": "Skills",
                "icon": "⚡",
                "title": "LLM Skill Evaluation",
                "description": "Evaluating all available tools against user intent",
                "elapsed_ms": int((time.time() - s_start) * 1000)
            })
            matched_skills = [{"skill_name": "all_tools", "text": "All registered tools enabled"}]

        elif skill_selector.startswith("Skill:"):
            target_skill = skill_selector.replace("Skill:", "").strip()
            matched_skills = [{"skill_name": target_skill, "text": f"User explicitly selected skill {target_skill}"}]
            steps.append({
                "component": "Skills",
                "icon": "⚡",
                "title": "Manual Skill Selected",
                "description": f"Using skill: {target_skill}",
                "elapsed_ms": int((time.time() - s_start) * 1000)
            })

        # 2. Execution Loop
        turn = 0
        context_history = []
        final_answer = ""
        current_observation = ""

        # Limit to top 2 skills if multiple found
        active_skills = matched_skills[:2]

        while turn < max_turns:
            turn += 1
            loop_start = time.time()

            if not active_skills:
                # No skill found: direct assistant prompt
                sys_prompt = "You are a helpful, accurate AI assistant. Answer the user question clearly and concisely."
                user_prompt = f"User Question: {message}"
                res_text, _, _, dur = self.call_llm(user_prompt, sys_prompt, model, temperature, max_tokens, custom_endpoint, conversation_id)
                final_answer = res_text
                steps.append({
                    "component": "LLM",
                    "icon": "🧠",
                    "title": "Direct Assistant Synthesis",
                    "description": f"Answered directly without tools ({dur}ms)",
                    "elapsed_ms": dur
                })
                break

            # Skills present: determine if tool should be executed
            skill_context_str = "\n\n".join([f"Skill: {s.get('skill_name', 'tool')}\n{s.get('text', '')}" for s in active_skills])
            system_prompt = (
                "You are an intelligent agent orchestrator with access to procedural tools.\n"
                "Review the user query and available skills. If you need more information or if a tool should be executed, "
                "respond ONLY with a JSON object specifying the tool and arguments. For example:\n"
                "{\n"
                '  "tool": "person_search.query_person_registry",\n'
                '  "arguments": {\n'
                '    "keyword": "Lucas Dubois",\n'
                '    "field": "name"\n'
                "  }\n"
                "}\n"
                "Available tools: \n"
                "- person_search.query_person_registry (arguments: keyword, field)\n"
                "- stock_search.query_stocks (arguments: action ['gainers', 'losers', 'quote'], limit, ticker)\n"
                "- time_weather.get_current_weather (arguments: city)\n"
                "- doc_search.query_documents (arguments: query, limit)\n\n"
                "If you already have enough information to answer the question completely, DO NOT output JSON. "
                "Instead, output your complete final answer to the user."
            )

            prompt_content = f"User Query: {message}\n\nAvailable Skills:\n{skill_context_str}\n"
            if context_history:
                prompt_content += "\nPrevious Observations:\n" + "\n".join(context_history) + "\n"

            llm_res, in_tok, out_tok, dur_ms = self.call_llm(
                prompt_content, system_prompt, model, temperature, max_tokens, custom_endpoint, conversation_id
            )

            # Check if LLM outputted JSON tool call
            tool_call = None
            try:
                # Look for JSON block or JSON brackets
                json_match = re.search(r"\{[\s\S]*\"tool\"[\s\S]*\}", llm_res)
                if json_match:
                    tool_call = json.loads(json_match.group(0))
            except Exception:
                tool_call = None

            if tool_call and "tool" in tool_call and turn < max_turns:
                t_name = tool_call["tool"]
                t_args = tool_call.get("arguments", {})

                steps.append({
                    "component": "LLM",
                    "icon": "🧠",
                    "title": f"Turn {turn}: Tool Decision",
                    "description": f"Decided to invoke {t_name}",
                    "elapsed_ms": dur_ms,
                    "payload": tool_call
                })

                # Execute Tool
                t_start = time.time()
                tool_result = None

                if "doc" in t_name.lower():
                    # Query doc_RAG
                    try:
                        rag_url = self._resolve(self.doc_rag_url, "doc_rag", 8003)
                        r = requests.post(f"{rag_url}/api/rag/query", json={
                            "db_type": "document",
                            "query": t_args.get("query", message),
                            "threshold": doc_threshold,
                            "limit": max_chunks,
                            "conversation_id": conversation_id,
                            "api_key": api_key
                        }, timeout=5)
                        tool_result = r.json()
                    except Exception as e:
                        tool_result = {"error": str(e)}
                    comp_name = "RAG"
                    comp_icon = "📚"
                else:
                    # Query Tools container
                    try:
                        tools_url = self._resolve(self.tools_url, "tools", 8005)
                        r = requests.post(f"{tools_url}/api/tools/call", json={
                            "tool": t_name,
                            "arguments": t_args,
                            "conversation_id": conversation_id,
                            "api_key": api_key
                        }, timeout=8)
                        tool_result = r.json().get("result", {})
                    except Exception as e:
                        tool_result = {"error": str(e)}
                    comp_name = "Tools"
                    comp_icon = "🔧"

                t_dur = int((time.time() - t_start) * 1000)
                obs_str = f"Observation from {t_name}: {json.dumps(tool_result)}"
                context_history.append(obs_str)

                steps.append({
                    "component": comp_name,
                    "icon": comp_icon,
                    "title": f"Executed {t_name}",
                    "description": f"Received result in {t_dur}ms",
                    "elapsed_ms": t_dur,
                    "result": tool_result
                })
            else:
                # LLM outputted final answer
                final_answer = llm_res
                steps.append({
                    "component": "LLM",
                    "icon": "🧠",
                    "title": f"Turn {turn}: Synthesis Complete",
                    "description": f"Generated final answer ({dur_ms}ms)",
                    "elapsed_ms": dur_ms
                })
                break

        # If loop reached max turns without breaking, make final call
        if not final_answer:
            final_sys = "You are a helpful assistant. Synthesize the final answer based on the collected context."
            final_p = f"User Query: {message}\n\nInformation Collected:\n" + "\n".join(context_history)
            final_answer, _, _, dur_ms = self.call_llm(final_p, final_sys, model, temperature, max_tokens, custom_endpoint, conversation_id)
            steps.append({
                "component": "LLM",
                "icon": "🧠",
                "title": "Final Synthesis",
                "description": f"Completed turn limit response ({dur_ms}ms)",
                "elapsed_ms": dur_ms
            })

        total_elapsed = int((time.time() - agent_start) * 1000)

        # Log Final Response
        self.log(
            invoker="Custom Agent",
            recipient="Web UI",
            event_type="chat_response",
            desc=f"Agent response completed in {total_elapsed}ms",
            payload={"response": final_answer, "steps_count": len(steps)},
            conv_id=conversation_id,
            dur_ms=total_elapsed
        )

        return {
            "conversation_id": conversation_id,
            "response": final_answer,
            "agent_type": "Custom Agent",
            "model": model,
            "elapsed_ms": total_elapsed,
            "steps": steps
        }
