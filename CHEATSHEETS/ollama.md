# Ollama CLI Cheat Sheet (English)

## 🚀 Basics

### ▶️ Run a model (chat mode)

``` bash
ollama run llama3
```

### 💬 One-shot prompt

``` bash
ollama run llama3 "Explain async in Python"
```

------------------------------------------------------------------------

## 📦 Model Management

### 📥 Pull a model

``` bash
ollama pull llama3
```

### 📋 List models

``` bash
ollama list
```

### ❌ Remove a model

``` bash
ollama rm llama3
```

------------------------------------------------------------------------

## 🔍 Model Info

### ℹ️ Show model details

``` bash
ollama show llama3
```

------------------------------------------------------------------------

## 🧠 Create Your Own Model

### 📄 Modelfile

``` txt
FROM llama3
SYSTEM You are a senior Python engineer.
```

### 🏗️ Build model

``` bash
ollama create my-model -f Modelfile
```

### ▶️ Run model

``` bash
ollama run my-model
```

------------------------------------------------------------------------

## 🔄 Update Model

``` bash
ollama pull llama3
```

------------------------------------------------------------------------

## 🌐 API

### ▶️ Start server

``` bash
ollama serve
```

Default endpoint:

    http://localhost:11434

### 📡 Curl request

``` bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3",
  "prompt": "Write a Python function for quicksort"
}'
```

------------------------------------------------------------------------

## ⚙️ Useful

### 🔥 Use different model

``` bash
ollama run phi3
```

### 🧪 Debug mode

``` bash
OLLAMA_DEBUG=1 ollama run llama3
```

------------------------------------------------------------------------

## 🧹 Processes

### 📊 Running models

``` bash
ollama ps
```

### 🛑 Stop model

``` bash
ollama stop llama3
```

------------------------------------------------------------------------

## 💡 Tips

-   models run locally (RAM / VRAM)
-   bigger model = more resource usage
-   check active models:

``` bash
ollama ps
```
