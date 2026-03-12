# caldr - Distributed AI Inference Network

Turn any GPU into part of a free, open, uncensored AI network.
No cloud. No cost. No censorship. Owned by everyone.

## Vision

AI should belong to humanity, not corporations.

Caldr is a peer-to-peer network where anyone can share their GPU and anyone can run AI models completely free. Like BitTorrent did for files, Caldr does for AI inference.

The core insight: Instead of asking "does this node meet requirements?", we ask "given ALL available nodes, what is the fastest combination RIGHT NOW?" - a self-optimizing, live inference graph.

## How It Works

User sends prompt
       down
Coordinator scores all nodes (VRAM + ping + reliability)
       down
Request routes to best available node
       down
If node fails, instant seamless failover
       down
Answer returns fast

## Features

- Smart routing - every node scored by VRAM, ping, and reliability in real time
- Seamless failover - node dies mid-request? Another picks up instantly
- Pipeline parallelism - 100 users served simultaneously across all nodes
- Model sharding - split large models across multiple smaller GPUs
- Web interface - chat in browser, free and decentralized
- No minimums - 1GB VRAM? You can still contribute
- No crypto - no tokens, no blockchain, just free compute

## Quick Start

### Join as a Node (Windows)

    irm https://raw.githubusercontent.com/keshavaraj-bit/caldr/main/install.ps1 | iex

### Join as a Node (Linux/Mac)

    curl -fsSL https://raw.githubusercontent.com/keshavaraj-bit/caldr/main/install.sh | bash

### Manual Install

    pip install fastapi uvicorn httpx psutil
    ollama pull phi3
    python node.py

### Run Your Own Coordinator

    pip install fastapi uvicorn httpx psutil
    python server.py

### Use the Network

Open web.html in your browser or use the API:

    curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d "{\"prompt\": \"Hello!\", \"model\": \"phi3\"}"

## Architecture

    caldr/
    - server.py       Coordinator - smart routing, failover, parallelism
    - node.py         Node - shares your GPU with the network
    - node_shard.py   Shard node - for splitting large models
    - client.py       CLI client - send prompts from terminal
    - web.html        Web UI - chat interface in browser
    - install.ps1     One-click installer for Windows
    - install.sh      One-click installer for Linux/Mac

## Node Scoring Algorithm

    score = (vram_free x 0.4) + (1000/ping_ms x 0.4) + (success_rate x 0.2)

Updated after every request. Best score always wins.

## Supported Models

| Model      | Size  | Min VRAM |
|------------|-------|----------|
| phi3       | 2.2GB | 3GB      |
| gemma:2b   | 1.5GB | 2GB      |
| mistral    | 4.1GB | 5GB      |
| llama3     | 4.7GB | 6GB      |
| llama3:70b | 40GB  | split    |

## Roadmap

- DONE V0.1 Single node inference
- DONE V0.2 Multi-node coordinator
- DONE V0.3 Smart node scoring
- DONE V0.4 Model sharding
- DONE V0.7 Seamless failover
- DONE V0.8 Pipeline parallelism
- DONE V1.0 Web UI + one-click installer
- NEXT V2.0 Fully decentralized (no central coordinator)
- NEXT V2.1 Mobile nodes
- NEXT V2.2 Browser nodes (WebGPU)
- NEXT V3.0 Distributed training

## The License Philosophy

Any model trained on this network must remain open source and uncensored.

This is the Compute Commons principle: you contribute your GPU, you get access.
Models built with the peoples compute belong to the people.

## Contributing

Built by one person with a laptop and a mission.

If you believe AI should be free and uncensored:
- Code - open a PR
- GPU - run a node
- Ideas - open an issue
- Spread - share the project

## License

MIT - free forever, open forever.

Built with a 3050 laptop GPU and a belief that AI belongs to everyone.
