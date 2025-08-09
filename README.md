<p align="center">
  <strong>English</strong> | <a href="README_JA.md">日本語</a> | <a href="README_ZH.md">简体中文</a>
</p>

# BookWith – A New Reading Experience with AI

> A next-generation conversational reading platform that goes beyond traditional e-book readers

<p align="center">
  <img src="https://img.shields.io/badge/AI-Multi_LLM-blue" alt="Multi-LLM AI Powered" />
  <img src="https://img.shields.io/badge/Languages-EN_|_JA_|_ZH-red" alt="Multi-language Support" />
  <img src="https://img.shields.io/badge/Platform-Web-green" alt="Web Platform" />
  <img src="https://img.shields.io/badge/Feature-AI_Podcast-purple" alt="AI Podcast Generation" />
</p>

## 📖 What is BookWith?

BookWith is an innovative e-book reader where AI becomes your reading partner. By conversing with an AI that fully understands the book's content in real time, BookWith transforms the reading experience from merely _consuming information_ to _creating knowledge_.

It is more than an e-book reader: BookWith answers your questions, deepens comprehension, and offers new perspectives—your true companion for reading.

https://github.com/user-attachments/assets/71ea703a-1213-4942-a355-5dc52f6b505d

## 🎯 Why BookWith?

### Pain Points of Conventional E-Book Readers

- ❌ When you encounter something unclear you have to look it up yourself
- ❌ No way to check how well you understand what you've read
- ❌ Hard to discover relationships with content you read in the past
- ❌ Notes and highlights are scattered and hard to utilize

### How BookWith Solves These Problems

- ✅ AI answers your questions on the spot
- ✅ Dialogue helps verify and deepen your understanding
- ✅ Automatically links to your past reading content
- ✅ Integrates annotations and AI dialogue into solid knowledge

## 🚀 Key Features

### 📚 **AI Reading Assistant**

**An AI partner that fully understands the book's content**

- **Context Awareness**: Grasps the content of the page you are on and answers in context
- **Instant Answers**: Real-time responses to questions such as "What does this term mean?" or "Summarize the author's argument."
- **Deep Insight Support**: Enables advanced discussions like "How can this concept be applied today?"
- **Full Japanese Support**: Natural Japanese dialogue with rich explanations of technical terms

**Example**

```
User: "If we apply the theory explained in this chapter to a real business scene, what happens?"
AI:   "Applying the innovation theory from Chapter 3 to actual business would…"
```

### 🎙️ **AI Podcast Generation**

**Convert book content into conversational podcasts**

https://github.com/user-attachments/assets/c4288075-a83c-4b52-a5c0-55b1a79ee252

- **Automatic Script Generation**: Extract key points and convert them into a host-guest dialogue format

  - Optimized for 5-10 minute listenable length
  - Explains complex topics in an easy-to-understand conversational style

- **High-Quality Audio Synthesis**: Utilize Google Cloud Text-to-Speech's multi-speaker functionality

  - Achieves natural conversation rhythm and intonation
  - Supports both Japanese and English
  - Supports multiple languages

- **Seamless Experience**:
  - Upload a book and automatically generate a podcast
  - Generated audio is immediately playable
  - Learn key points while commuting or during movement

**Use Cases**

- When you want to understand the summary of a long novel
- Check the key points of a business book while commuting
- Preview the main ideas of a technical book with audio

### 🧠 **Multi-Layer Memory System**

**Innovative memory management that ensures continuity in your reading**

- **Short-Term Memory (latest 5 entries)**
  - Maintains the current conversation flow
  - Keeps context even when you turn pages
- **Mid-Term Memory (summary every 20 entries)**
  - Condenses key discussion points
  - Sustains understanding across chapters
- **Long-Term Memory (vector search)**
  - Automatically retrieves relevant information from all past dialogues
  - Links with learning from other books
- **User Profile**
  - Learns your interests and preferences
  - Provides a personalized reading experience

_Example_: Content from an economics book you read a week ago is automatically linked to the marketing book you are reading now.

### 🎨 **Smart Annotation**

**Advanced highlighting that visualizes your thinking**

- **Color Highlights (5 colors)**

  - 🔴 Red: Critical points
  - 🟡 Yellow: Important concepts
  - 🟢 Green: Ideas to practice
  - 🔵 Blue: Questions / To-verify

- **Intelligent Notes**

  - Add detailed comments to highlighted text
  - Supports Markdown formatting

- **AI Integration**
  - Automatically prompts AI questions about highlighted passages
  - AI understands notes and provides related information
  - Analyzes across multiple highlights

**Use Cases**

- Highlight crucial quotes while reading a paper → AI suggests related studies
- Mark actionable points in a business book with green → Discuss an implementation plan with AI

### 🔍 **Semantic Search**

**Revolutionary information discovery connected by meaning**

- **Cross-Book Search**

  - Search across multiple books
  - Past dialogue history is also indexed
  - Includes annotation content for comprehensive search

- **Automatic Linking**
  - Suggests past reading content related to what you are reading now
  - E.g. "This concept also appeared in the book ○○ you read three months ago…"

## 👥 Perfect For

### 🎓 **Researchers & Graduate Students**

- AI proposes related research while you read papers
- Confirm complex theories on the spot
- Integrated quote management and literature notes

### 📖 **Book Lovers**

- Ask AI about character relationships in novels
- Get historical background or cultural context explained
- Organize discussion points for book clubs

### 🎒 **Students & Examinees**

- Instant explanations for unclear textbook sections
- Work through practice problems with AI
- Integrate content from multiple reference books

### 💼 **Business Professionals**

- Consult on applying business book concepts to your company
- Summaries of key points and action plan creation
- Consolidates knowledge from multiple business books

## 📱 How to Use (Detailed Steps)

### Step 1: Upload a Book

1. Drag-and-drop or select an ePub file
2. It is added to your library and ready to read immediately

### Step 2: Read & Highlight

1. Select important text while reading
2. Choose from 5 highlight colors
3. Add notes if necessary
4. Ask AI about highlighted content

### Step 3: Chat with AI

1. Ask questions anytime in the chat panel on the right
2. Select text → "Ask AI" to pose context-aware questions
3. Continue discussions based on past dialogue history
4. Conversations are automatically saved and indexed

### Step 4: Leverage Your Knowledge

1. Review past learning with semantic search
2. Integrate knowledge from multiple books
3. Export your learning for external use

## 💻 Environment & Technical Specs

- **Supported Devices**
  - PC (Windows 10+, macOS 10.15+)
  - Tablets (iPad, Android tablets)
  - Smartphones (responsive design)
- **Requirements**
  - Internet connection (for AI features)
  - JavaScript enabled
- **Supported Formats**
  - ePub 2.0
  - ePub 3.0

## �️ Local Setup

Want to run BookWith on your own computer?

📋 **[Local Setup Guide](docs/DEVELOPMENT_GUIDE.md)** - Complete installation instructions

The setup guide includes:

- System requirements and prerequisites
- Step-by-step installation process
- How to configure your environment
- Troubleshooting common setup issues
- Getting started with your first book

---

## Acknowledgements

This project is developed as a fork of [Flow](https://github.com/pacexy/flow). We are grateful for the excellent foundation provided by the original project.

<p align="center">
  <strong>BookWith – Read deeper. Enjoy more.</strong>
</p>

<p align="center">
  <sub>© 2025 BookWith. All rights reserved.</sub>
</p>
