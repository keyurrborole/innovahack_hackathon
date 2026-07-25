import { useState, useRef, useEffect } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { MessageCircle, X, Send, Bot, User } from 'lucide-react';
import { ScrollArea } from './ui/scroll-area';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const ChatBot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content:
        "Hello! I'm FlowAssist, your fund-flow investigation assistant for this PS3 prototype. Ask about layering, round-tripping, structuring, dormant accounts, profile mismatch, or how the graph and ML scores work.",
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const userInput = input;
    setInput('');
    setIsLoading(true);

    try {
      // Call Google Gemini API directly
      const GEMINI_API_KEY = 'AIzaSyAVzE1E-Hle0xQwF513oKct-CJTgqeVmQo';
      const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=${GEMINI_API_KEY}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          contents: [{
            parts: [{
              text: `You are FlowAssist, an assistant for FundFlow Trace—a bank internal fund-flow tracking prototype (PS3) for fraud detection.

Context:
- Maps transfers across accounts, products, branches, channels as a graph
- Flags: rapid layering, circular (round-trip) flows, structuring under thresholds, dormant account spikes, KYC/behavior profile mismatch
- Uses graph analytics + ML suspicion scores; supports investigator trace and FIU-oriented evidence packages
- Demo stack: FastAPI backend, React dashboard, sample subgraph visualizations

User question: ${userInput}

Answer concisely (under 150 words) in plain language about internal fund-flow fraud, graph detection, or how investigators would use this prototype.`
            }]
          }],
          generationConfig: {
            temperature: 0.7,
            maxOutputTokens: 500,
          }
        })
      });

      let assistantResponse = '';
      
      if (response.ok) {
        const data = await response.json();
        assistantResponse = data.candidates?.[0]?.content?.parts?.[0]?.text || 'I apologize, but I encountered an error. Please try asking your question again.';
      } else {
        // Fallback response if API fails
        assistantResponse = getSmartResponse(userInput);
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: assistantResponse,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      // Fallback for demo
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: getSmartResponse(userInput),
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const getSmartResponse = (query: string): string => {
    const lowerQuery = query.toLowerCase();
    
    if (lowerQuery.includes('smurfing') || lowerQuery.includes('layering')) {
      return 'Rapid layering moves funds through many internal accounts or products in a short time to obscure origin. In FundFlow Trace we score paths by hop count, time windows, and amount residuals, and surface the subgraph for analysts.';
    }

    if (lowerQuery.includes('gnn') || lowerQuery.includes('neural network')) {
      return 'The prototype combines graph features (centrality, cycles, velocity) with ML layers to rank accounts and subgraphs. That helps prioritize alerts while keeping rule-based explanations for investigators.';
    }

    if (lowerQuery.includes('price') || lowerQuery.includes('cost') || lowerQuery.includes('pricing')) {
      return 'This build is a hackathon/demo prototype—pricing is not applicable. In production, costs would depend on data volume, deployment (on-prem vs cloud), and integration with core banking and case tools.';
    }

    if (lowerQuery.includes('api') || lowerQuery.includes('integrate')) {
      return 'The repo includes a FastAPI backend (upload, analysis, graph, reports) and a React dashboard. Integration points for production would be core-banking feeds, identity/KYC stores, and your case management system.';
    }

    if (lowerQuery.includes('data') || lowerQuery.includes('format') || lowerQuery.includes('upload')) {
      return 'Use ledger-style rows: source account, destination account, amount, value date, product, branch, channel. The pipeline turns that into a fund-flow graph for visualization and detection.';
    }

    if (lowerQuery.includes('accuracy') || lowerQuery.includes('detection rate')) {
      return 'Reported metrics in the UI are illustrative for the demo. Real precision/recall would be validated on labeled bank investigations and tuned with your policy thresholds.';
    }

    if (lowerQuery.includes('help') || lowerQuery.includes('how') || lowerQuery.includes('what')) {
      return 'Try asking about: layering vs round-tripping, structuring near thresholds, dormant accounts, profile mismatch, FIU evidence export, or how the fund-flow graph is built.';
    }

    return 'Ask about internal fund-flow fraud patterns, graph + ML detection, or investigator workflows in this PS3 prototype.';
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <>
      {/* Chat Button */}
      {!isOpen && (
        <Button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 h-14 w-14 rounded-full bg-crypto-purple hover:bg-crypto-dark-purple shadow-lg z-50 transition-all duration-300 hover:scale-110"
          size="icon"
        >
          <MessageCircle className="h-6 w-6" />
        </Button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-96 h-[600px] bg-crypto-blue border border-white/10 rounded-2xl shadow-2xl z-50 flex flex-col overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-crypto-purple to-crypto-dark-purple p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 bg-white/20 rounded-full flex items-center justify-center">
                <Bot className="h-6 w-6 text-white" />
              </div>
              <div>
                <h3 className="text-white font-semibold">FlowAssist</h3>
                <p className="text-xs text-white/80">Fund-flow investigation (demo)</p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsOpen(false)}
              className="text-white hover:bg-white/20"
            >
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Messages */}
          <ScrollArea className="flex-1 p-4" ref={scrollRef}>
            <div className="space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex gap-3 ${
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  {message.role === 'assistant' && (
                    <div className="h-8 w-8 bg-crypto-purple/20 rounded-full flex items-center justify-center flex-shrink-0">
                      <Bot className="h-4 w-4 text-crypto-purple" />
                    </div>
                  )}
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-2 ${
                      message.role === 'user'
                        ? 'bg-crypto-purple text-white'
                        : 'bg-white/5 text-gray-200 border border-white/10'
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    <p className="text-xs opacity-60 mt-1">
                      {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                  {message.role === 'user' && (
                    <div className="h-8 w-8 bg-white/10 rounded-full flex items-center justify-center flex-shrink-0">
                      <User className="h-4 w-4 text-white" />
                    </div>
                  )}
                </div>
              ))}
              {isLoading && (
                <div className="flex gap-3">
                  <div className="h-8 w-8 bg-crypto-purple/20 rounded-full flex items-center justify-center">
                    <Bot className="h-4 w-4 text-crypto-purple animate-pulse" />
                  </div>
                  <div className="bg-white/5 border border-white/10 rounded-2xl px-4 py-2">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>

          {/* Input */}
          <div className="p-4 border-t border-white/10">
            <div className="flex gap-2">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me anything..."
                className="bg-white/5 border-white/10 text-white placeholder:text-gray-400"
                disabled={isLoading}
              />
              <Button
                onClick={handleSendMessage}
                disabled={isLoading || !input.trim()}
                className="bg-crypto-purple hover:bg-crypto-dark-purple"
                size="icon"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default ChatBot;
