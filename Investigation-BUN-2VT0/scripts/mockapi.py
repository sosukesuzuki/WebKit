#!/usr/bin/env python3
# Minimal mock of the Anthropic Messages API (streaming) that drives Claude Code through tool_use turns.
import json, http.server, socketserver, itertools, sys, threading, time
PORT=int(sys.argv[1]) if len(sys.argv)>1 else 8787
counter=itertools.count()
TOOLS=[("Read", {"file_path":"/tmp/ccwork/a.txt"}),
       ("Glob", {"pattern":"**/*.txt","path":"/tmp/ccwork"}),
       ("Grep", {"pattern":"hello","path":"/tmp/ccwork"}),
       ("Read", {"file_path":"/tmp/ccwork/big.txt"}),
       ("Glob", {"pattern":"**/*","path":"/tmp/ccwork"}),
       ("Grep", {"pattern":"line [0-9]+","path":"/tmp/ccwork","output_mode":"content"})]
class H(http.server.BaseHTTPRequestHandler):
    protocol_version="HTTP/1.1"
    def log_message(self,fmt,*a): sys.stderr.write((fmt%a)+'\n'); sys.stderr.flush()
    def do_GET(self):
        self.send_response(200); self.send_header("Content-Type","application/json"); b=b'{"data":[]}'; self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_POST(self):
        n=int(self.headers.get("Content-Length","0")); body=self.rfile.read(n)
        try: req=json.loads(body)
        except Exception: req={}
        msgs=req.get("messages",[])
        # count tool_result blocks so far to decide next step
        tool_turns=0
        for m in msgs:
            c=m.get("content")
            if isinstance(c,list):
                tool_turns+=sum(1 for b in c if isinstance(b,dict) and b.get("type")=="tool_result")
        i=next(counter)
        stream=req.get("stream",False)
        avail={t.get("name") for t in req.get("tools",[])} if isinstance(req.get("tools"),list) else set()
        use_tool=None
        if tool_turns < int(__import__('os').environ.get('MOCK_TOOL_TURNS','40')):
            for name,inp in TOOLS[tool_turns%len(TOOLS):]+TOOLS:
                if not avail or name in avail: use_tool=(name,inp); break
        mid=f"msg_{i}"
        def ev(t,d):
            d=dict(d); d["type"]=t
            return f"event: {t}\ndata: {json.dumps(d)}\n\n".encode()
        out=[]
        out.append(ev("message_start",{"message":{"id":mid,"type":"message","role":"assistant","model":req.get("model","claude-mock"),"content":[],"stop_reason":None,"stop_sequence":None,"usage":{"input_tokens":10,"output_tokens":1}}}))
        text="Working on it... step %d. "%tool_turns + "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "*60 + "```js\nfunction f(a,b){return a+b}\n```\n"*10
        out.append(ev("content_block_start",{"index":0,"content_block":{"type":"text","text":""}}))
        for k in range(0,len(text),37):
            out.append(ev("content_block_delta",{"index":0,"delta":{"type":"text_delta","text":text[k:k+37]}}))
        out.append(ev("content_block_stop",{"index":0}))
        if use_tool:
            name,inp=use_tool
            tid=f"toolu_{i}"
            out.append(ev("content_block_start",{"index":1,"content_block":{"type":"tool_use","id":tid,"name":name,"input":{}}}))
            js=json.dumps(inp)
            for k in range(0,len(js),23):
                out.append(ev("content_block_delta",{"index":1,"delta":{"type":"input_json_delta","partial_json":js[k:k+23]}}))
            out.append(ev("content_block_stop",{"index":1}))
            out.append(ev("message_delta",{"delta":{"stop_reason":"tool_use","stop_sequence":None},"usage":{"output_tokens":50}}))
        else:
            out.append(ev("message_delta",{"delta":{"stop_reason":"end_turn","stop_sequence":None},"usage":{"output_tokens":50}}))
        out.append(ev("message_stop",{}))
        if stream:
            self.send_response(200); self.send_header("Content-Type","text/event-stream"); self.send_header("Cache-Control","no-cache"); self.send_header("Transfer-Encoding","chunked"); self.end_headers()
            for chunk in out:
                self.wfile.write(b"%x\r\n%s\r\n"%(len(chunk),chunk)); self.wfile.flush()
            self.wfile.write(b"0\r\n\r\n"); self.wfile.flush()
        else:
            content=[{"type":"text","text":text}]
            if use_tool: content.append({"type":"tool_use","id":f"toolu_{i}","name":use_tool[0],"input":use_tool[1]})
            b=json.dumps({"id":mid,"type":"message","role":"assistant","model":"claude-mock","content":content,"stop_reason":"tool_use" if use_tool else "end_turn","usage":{"input_tokens":10,"output_tokens":50}}).encode()
            self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
class S(socketserver.ThreadingMixIn, http.server.HTTPServer): daemon_threads=True; allow_reuse_address=True
S(("127.0.0.1",PORT),H).serve_forever()
